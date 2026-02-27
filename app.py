import streamlit as st
import pikepdf
import tempfile
import zipfile
import os
import gc

st.set_page_config(page_title="Heavy Duty PDF Splitter", layout="centered")

def split_pdf_on_disk(uploaded_file, split_mode, value):
    # 1. Create a temporary folder on the DISK (Not RAM)
    temp_dir = tempfile.mkdtemp()
    
    # 2. Save the uploaded massive file to the hard drive immediately
    input_pdf_path = os.path.join(temp_dir, "input.pdf")
    with open(input_pdf_path, "wb") as f:
        # getbuffer() uses less memory than getvalue()
        f.write(uploaded_file.getbuffer()) 
    
    zip_path = os.path.join(temp_dir, "split_pdfs.zip")
    
    # 3. Read from disk to save RAM
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

        # 4. Create ZIP directly on disk
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            
            # Progress bar for the user
            progress_bar = st.progress(0)
            
            for idx, (start, end) in enumerate(ranges):
                new_pdf = pikepdf.Pdf.new()
                
                # Faster page append
                new_pdf.pages.extend(pdf.pages[start:end]) 
                
                chunk_name = f"Harrison_Part_{idx+1}_Pages_{start+1}-{end}.pdf"
                chunk_path = os.path.join(temp_dir, chunk_name)
                
                # Save chunk to disk, NOT memory
                new_pdf.save(chunk_path)
                new_pdf.close()
                
                # Write to zip
                zipf.write(chunk_path, arcname=chunk_name)
                
                # Delete the unzipped chunk immediately to save space
                os.remove(chunk_path)
                gc.collect() # Force RAM cleanup
                
                # Update progress
                progress_bar.progress((idx + 1) / len(ranges))
                
    return zip_path, total_pages

st.title("📚 Heavy Duty PDF Splitter")
st.write("Optimized to split massive medical books (like Harrison's) without crashing.")

uploaded_file = st.file_uploader("Upload massive PDF here", type="pdf")

if uploaded_file:
    col1, col2 = st.columns(2)
    with col1:
        mode = st.radio("Split Method",["By Page Interval", "By Number of Slices"])
    with col2:
        if mode == "By Page Interval":
            val = st.number_input("Pages per PDF", min_value=1, value=500)
        else:
            val = st.number_input("Total number of slices", min_value=1, value=4)

    if st.button("🚀 Process & Split (Disk Mode)"):
        with st.spinner("Processing massive file... Please wait. Do not refresh."):
            try:
                # Run disk-based splitting
                zip_path, total_pages = split_pdf_on_disk(uploaded_file, mode, val)
                
                st.success(f"Success! Processed {total_pages} pages.")
                
                # Provide download directly from disk file
                with open(zip_path, "rb") as fp:
                    st.download_button(
                        label="⬇️ Download Split PDFs (ZIP)",
                        data=fp,
                        file_name="split_textbook.zip",
                        mime="application/zip"
                    )
            except Exception as e:
                st.error(f"Error: {e}")
