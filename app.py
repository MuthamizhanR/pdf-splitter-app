import streamlit as st
import pikepdf
import io
import zipfile
import os
import gc

st.set_page_config(page_title="Pro PDF Splitter", layout="centered")

def split_pdf_logic(uploaded_file, split_mode, value):
    # Use pikepdf for efficiency
    with pikepdf.open(uploaded_file) as pdf:
        total_pages = len(pdf.pages)
        output_files = []
        
        # Define page ranges based on mode
        ranges = []
        if split_mode == "By Page Interval":
            # e.g., Every 10 pages
            for i in range(0, total_pages, value):
                ranges.append((i, min(i + value, total_pages)))
        else:
            # e.g., Into 5 slices
            pages_per_slice = total_pages // value
            for i in range(value):
                start = i * pages_per_slice
                # Ensure the last slice gets the remaining pages
                end = (i + 1) * pages_per_slice if i != value - 1 else total_pages
                if start < total_pages:
                    ranges.append((start, end))

        # Perform the split
        for idx, (start, end) in enumerate(ranges):
            new_pdf = pikepdf.Pdf.new()
            for i in range(start, end):
                new_pdf.pages.append(pdf.pages[i])
            
            # Save to memory buffer
            out_buffer = io.BytesIO()
            new_pdf.save(out_buffer)
            output_files.append((f"part_{idx+1}.pdf", out_buffer.getvalue()))
            new_pdf.close()
            
    return output_files

st.title("📂 Pro PDF Splitter")
st.write("Split large PDFs (up to 500MB) by intervals or fixed slices.")

uploaded_file = st.file_uploader("Upload your PDF", type="pdf")

if uploaded_file:
    # Memory optimization: Clear old variables
    gc.collect()
    
    with pikepdf.open(uploaded_file) as pdf:
        total_pages = len(pdf.pages)
    
    st.info(f"Total Pages: {total_pages} | File Size: {uploaded_file.size / (1024*1024):.2f} MB")
    
    col1, col2 = st.columns(2)
    with col1:
        mode = st.radio("Split Method", ["By Page Interval", "By Number of Slices"])
    with col2:
        if mode == "By Page Interval":
            val = st.number_input("Pages per PDF", min_value=1, max_value=total_pages, value=10)
        else:
            val = st.number_input("Total number of slices", min_value=1, max_value=total_pages, value=2)

    if st.button("🚀 Process & Split"):
        with st.spinner("Splitting PDF... This may take a moment for large files."):
            try:
                # 1. Split the PDF
                results = split_pdf_logic(uploaded_file, mode, val)
                
                # 2. Package into a ZIP in-memory
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    for filename, data in results:
                        zf.writestr(filename, data)
                
                # 3. Provide download button
                st.success(f"Successfully split into {len(results)} parts!")
                st.download_button(
                    label="⬇️ Download All as ZIP",
                    data=zip_buffer.getvalue(),
                    file_name="split_pdfs.zip",
                    mime="application/zip"
                )
                
                # Force cleanup
                del results
                gc.collect()
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
