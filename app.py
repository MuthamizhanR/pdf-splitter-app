import streamlit as st
import pikepdf
import os
import gc

st.set_page_config(page_title="Heavy Duty PDF Splitter", layout="centered")

def split_pdf_direct_save(uploaded_file, split_mode, value):
    # 1. Create a folder right next to this script on your computer
    output_dir = os.path.join(os.getcwd(), "Split_Harrison_Books")
    os.makedirs(output_dir, exist_ok=True)
    
    # 2. Save the uploaded file to disk temporarily to save RAM
    input_pdf_path = os.path.join(output_dir, "temp_input.pdf")
    with open(input_pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer()) 
    
    # 3. Read and Split
    with pikepdf.open(input_pdf_path) as pdf:
        total_pages = len(pdf.pages)
        
        # Calculate slices
        ranges =[]
        if split_mode == "By Page Interval":
            for i in range(0, total_pages, value):
                ranges.append((i, min(i + value, total_pages)))
        else:
            pages_per_slice = total_pages // value
            for i in range(value):
                start = i * pages_per_slice
                end = (i + 1) * pages_per_slice if i != value - 1 else total_pages
                if start < total_pages:
                    ranges.append((start, end))

        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 4. Save directly to the folder (No ZIP, No Download Button!)
        for idx, (start, end) in enumerate(ranges):
            new_pdf = pikepdf.Pdf.new()
            new_pdf.pages.extend(pdf.pages[start:end]) 
            
            chunk_name = f"Harrison_Part_{idx+1}_Pages_{start+1}-{end}.pdf"
            chunk_path = os.path.join(output_dir, chunk_name)
            
            # Save straight to computer drive
            new_pdf.save(chunk_path)
            new_pdf.close()
            
            gc.collect() # Clean RAM
            
            # Update UI
            progress_bar.progress((idx + 1) / len(ranges))
            status_text.text(f"✅ Saved: {chunk_name} straight to folder!")
            
    # Clean up the temporary heavy input file
    os.remove(input_pdf_path)
    return output_dir, total_pages

st.title("📚 Heavy Duty PDF Splitter (Local Export)")
st.write("Bypasses browser downloads to safely split massive medical books.")

uploaded_file = st.file_uploader("Upload Harrison's PDF here", type="pdf")

if uploaded_file:
    col1, col2 = st.columns(2)
    with col1:
        mode = st.radio("Split Method",["By Page Interval", "By Number of Slices"])
    with col2:
        if mode == "By Page Interval":
            val = st.number_input("Pages per PDF", min_value=1, value=500)
        else:
            val = st.number_input("Total number of slices", min_value=1, value=4)

    if st.button("🚀 Process & Save Directly to Computer"):
        with st.spinner("Processing massive file... Please wait."):
            try:
                # Run the direct-save function
                output_folder, total_pages = split_pdf_direct_save(uploaded_file, mode, val)
                
                st.success(f"🎉 Success! Processed {total_pages} pages.")
                st.info(f"📁 You don't need to download anything. Open the folder located at:\n\n**{output_folder}**\n\nYour split PDFs are already waiting inside!")
                st.balloons()
                
            except Exception as e:
                st.error(f"Error: {e}")
