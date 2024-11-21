import streamlit as st
import PyPDF2
import re
from urllib.parse import unquote
import pandas as pd
from io import BytesIO
from datetime import datetime
import base64

def extract_urls_from_pdf(pdf_file):
    """Extract URLs from PDF file uploaded through Streamlit"""
    urls = set()
    
    try:
        # Read PDF file
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        total_pages = len(pdf_reader.pages)
        
        # Create a progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Iterate through each page
        for page_num, page in enumerate(pdf_reader.pages, 1):
            status_text.text(f"Processing page {page_num}/{total_pages}")
            progress_bar.progress(page_num / total_pages)
            
            # Extract URLs from annotations
            if '/Annots' in page:
                annotations = page['/Annots']
                if annotations:
                    annotations = [annotation.get_object() for annotation in annotations]
                    
                    for annotation in annotations:
                        if annotation.get('/Subtype') == '/Link':
                            if '/A' in annotation:
                                action = annotation['/A']
                                if '/URI' in action:
                                    url = action['/URI']
                                    url = unquote(url)
                                    urls.add(url)
            
            # Extract URLs from text content
            text = page.extract_text()
            url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
            text_urls = re.findall(url_pattern, text)
            urls.update(text_urls)
        
        # Clear progress bar and status
        progress_bar.empty()
        status_text.empty()
        
        return sorted(list(urls))
        
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        return []

def get_download_link(urls, filename):
    """Generate a download link for the URLs"""
    df = pd.DataFrame(urls, columns=['URL'])
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV file</a>'
    return href

def main():
    st.set_page_config(
        page_title="PDF URL Extractor",
        page_icon="🔗",
        layout="wide"
    )
    
    st.title("🔗 PDF URL Extractor")
    st.write("Upload a PDF file to extract all hyperlinks")
    
    # File uploader
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None:
        # Create a container for the results
        with st.container():
            st.write("---")
            
            # Extract URLs
            with st.spinner('Extracting URLs...'):
                urls = extract_urls_from_pdf(uploaded_file)
            
            if urls:
                st.success(f"Found {len(urls)} unique URLs!")
                
                # Display URLs in a dataframe
                df = pd.DataFrame(urls, columns=['URL'])
                st.dataframe(
                    df,
                    column_config={
                        "URL": st.column_config.LinkColumn("URL")
                    },
                    hide_index=True
                )
                
                # Create columns for download options
                col1, col2 = st.columns(2)
                
                with col1:
                    # Download as CSV
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"urls_{timestamp}.csv"
                    st.markdown(get_download_link(urls, filename), unsafe_allow_html=True)
                
                with col2:
                    # Copy to clipboard button
                    if st.button("Copy URLs to clipboard"):
                        df['URL'].to_clipboard(index=False)
                        st.success("URLs copied to clipboard!")
            else:
                st.warning("No URLs found in the PDF.")
            
            # Display file details
            st.write("---")
            st.write("File Details:")
            file_details = {
                "Filename": uploaded_file.name,
                "File size": f"{uploaded_file.size / 1024:.2f} KB",
                "Upload time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            st.json(file_details)

if __name__ == "__main__":
    main()
