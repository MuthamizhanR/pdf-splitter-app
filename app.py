import streamlit as st
import pikepdf
import os
import tempfile
import gc

st.set_page_config(page_title="Tablet PDF Splitter", layout="centered")

# Set up a temporary folder on the cloud server
if "temp_dir" not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()
    st.session_state.processed_files =[]

def process_and_split(uploaded_file, split_mode, value):
    # 1. Save uploaded massive file to the cloud disk to save RAM
    input_pdf_path = os.path.join(st.session_state.temp_dir, "harrison_input.pdf")
    with open(input_pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer()) 
    
    output_files =[]
    
    # 2. Read from disk 
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
        
        # 3. Process each chunk and save to cloud disk temporarily
        for idx, (start, end) in enumerate(ranges):
            new_pdf = pikepdf.Pdf.new()
            new_pdf.pages.extend(pdf.pages[start:end]) 
            
            chunk_name = f"Harrison_Part_{idx+1}_Pages_{start+1}-{end}.pdf"
            chunk_path = os.path.join(st.session_state.temp_dir, chunk_name)
            
            new_pdf.save(chunk_path)
            new_pdf.close()
            
            output_files.append((chunk_name, chunk_path))
            gc.collect() # Keep Cloud RAM clean!
            
            progress_bar.progress((idx + 1) / len(ranges))
            
    # Save the list of files to session state so buttons don't disappear
    st.session_state.processed_files = output_files
    # Delete massive input file to free up cloud space
    os.remove(input_pdf_path)

st.title("📱 Tablet-Optimized PDF Splitter")
st.write("Designed for Streamlit Cloud. Downloads are split into parts so your tablet browser won't crash.")

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

    # Only show the process button if we haven't processed yet
    if not st.session_state.processed_files:
        if st.button("🚀 Process Book"):
            with st.spinner("Slicing massive book... Please keep this page open."):
                try:
                    process_and_split(uploaded_file, mode, val)
                    st.success("✅ Book successfully sliced!")
                    st.rerun() # Refresh page to show download buttons
                except Exception as e:
                    st.error(f"Error during processing: {e}")

# If files are processed, show individual download buttons!
if st.session_state.processed_files:
    st.write("### 📥 Download Your Split Files")
    st.info("Download them one by one to prevent your tablet browser from timing out.")
    
    for file_name, file_path in st.session_state.processed_files:
        # Open file directly from disk into the download button to save RAM
        with open(file_path, "rb") as f:
            st.download_button(
                label=f"⬇️ Download {file_name}",
                data=f,
                file_name=file_name,
                mime="application/pdf",
                key=file_name # Unique key for each button
            )
            
    if st.button("🗑️ Clear and Start Over"):
        st.session_state.processed_files =
