import streamlit as st
from pdf2image import convert_from_path
import tempfile
import os
import io
import zipfile
from PIL import Image
import subprocess

# Set to None so it uses the Poppler installation from the Dockerfile
poppler_path = None

st.set_page_config(page_title="PDF to Long Image Converter", layout="wide")
st.title("PDF→PNG")

st.info("Upload a PDF and choose to download as individual pages (ZIP) or a single combined image.")

# Option selector
combine_pages = st.radio(
    "Output format:",
    options=["Combined Long Image", "Individual Pages (ZIP)"],
    horizontal=True
)

# File uploader
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a temporary file path
        temp_pdf_path = os.path.join(temp_dir, uploaded_file.name)
        
        # Write the uploaded file's bytes to the temporary file
        with open(temp_pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.write("Converting PDF... please wait.")
        with st.spinner('Processing pages...'):
            try:
                # Convert PDF pages to images
                images = convert_from_path(
                    temp_pdf_path, 
                    poppler_path=poppler_path
                )
                
                st.success(f"Success! Converted {len(images)} pages.")

                # Get the base filename of the PDF
                base_filename = os.path.splitext(uploaded_file.name)[0]

                if combine_pages == "Combined Long Image":
                    # --- Combine images vertically ---
                    
                    # Get the width of the first image (assuming all pages have same width)
                    # If pages have different widths, we'll use the maximum width
                    widths = [img.width for img in images]
                    heights = [img.height for img in images]
                    
                    max_width = max(widths)
                    total_height = sum(heights)
                    
                    # Create a new blank image with the combined dimensions
                    combined_image = Image.new('RGB', (max_width, total_height), 'white')
                    
                    # Paste each page image into the combined image
                    y_offset = 0
                    for img in images:
                        # Center the image horizontally if it's narrower than max_width
                        x_offset = (max_width - img.width) // 2
                        combined_image.paste(img, (x_offset, y_offset))
                        y_offset += img.height
                    
                    # Save the combined image to a buffer
                    img_buffer = io.BytesIO()
                    combined_image.save(img_buffer, format="PNG")
                    img_buffer.seek(0)
                    
                    # Download button for the combined image
                    st.download_button(
                        label=f"Download Combined Image ({len(images)} pages, {max_width}×{total_height}px)",
                        data=img_buffer,
                        file_name=f"{base_filename}_combined.png",
                        mime="image/png",
                        use_container_width=True
                    )
                    
                    # Show preview (scaled down for display)
                    # st.subheader("Preview:")
                    # st.image(combined_image, caption=f"Combined image: {len(images)} pages", use_container_width=True)

                else:  # Individual Pages (ZIP)
                    # --- Create ZIP file with individual images ---
                    
                    # Create an in-memory buffer for the zip file
                    zip_buffer = io.BytesIO()
                    
                    # Create a zip file in the buffer
                    with zipfile.ZipFile(zip_buffer, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                        for i, image in enumerate(images):
                            page_num = i + 1
                            
                            # Create an in-memory buffer for the PNG image
                            img_buffer = io.BytesIO()
                            image.save(img_buffer, format="PNG")
                            img_buffer.seek(0)
                            
                            # Write the image from its buffer into the zip file
                            zf.writestr(f"page_{page_num}.png", img_buffer.read())
                    
                    # Rewind the zip buffer to the beginning
                    zip_buffer.seek(0)
                    
                    # Download button for ZIP file
                    st.download_button(
                        label=f"Download All {len(images)} Pages as ZIP",
                        data=zip_buffer,
                        file_name=f"{base_filename}_images.zip",
                        mime="application/zip",
                        use_container_width=True
                    )

            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.error("There was an issue processing the PDF with the Poppler backend.")