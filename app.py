import streamlit as st
import os
import tempfile
from markitdown import MarkItDown

st.set_page_config(page_title="Secure MarkItDown UI", layout="wide")
st.title("📄 Secure MarkItDown Converter")
st.write("Your files are processed locally and securely.")

uploaded_file = st.file_uploader(
    "Choose a file", 
    type=["pdf", "docx", "pptx", "xlsx", "html", "csv", "json", "xml"]
)

if uploaded_file:
    if st.button("🚀 Convert to Markdown", type="primary"):
        with st.spinner("Converting securely..."):
            # Safely extract only the file extension
            _, file_extension = os.path.splitext(uploaded_file.name)
            
            # Security Standard: Isolate file execution inside a secure OS temp directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Enforce a secure, randomized filename that ignores user input paths
                secure_temp_path = os.path.join(temp_dir, f"upload{file_extension}")
                
                with open(secure_temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                try:
                    md = MarkItDown()
                    # Use local conversion specifically
                    result = md.convert_local(secure_temp_path)
                    
                    st.success("Done!")
                    st.subheader("Preview Output:")
                    st.text_area("", result.text_content, height=350)
                    
                    # Safe download generation
                    output_name = os.path.splitext(uploaded_file.name)[0] + ".md"
                    st.download_button(
                        label="📥 Download Markdown File",
                        data=result.text_content,
                        file_name=output_name,
                        mime="text/markdown"
                    )
                except Exception as e:
                    st.error(f"An error occurred during secure processing: {e}")
                # The 'with' context manager automatically wipes the directory and data from disk here