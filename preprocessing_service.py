"""
PDF Preprocessing Service
Handles PDF validation and conversion to images for Textract compatibility.
Designed to run as a separate service (ECS/Fargate or Docker container).
"""

import logging
import os
import io
import asyncio
import time
import tempfile
from typing import Optional, Dict, Any, List, Tuple
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFPreprocessor:
    """PDF preprocessing service for Textract compatibility."""
    
    def __init__(self):
        """Initialize the preprocessor."""
        self.s3_client = None
        self._init_clients()
    
    def _init_clients(self):
        """Initialize AWS clients."""
        try:
            # Initialize S3 client
            if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
                # Running in Lambda - use IAM role
                self.s3_client = boto3.client('s3')
            else:
                # Running locally or in container - use credentials if available
                self.s3_client = boto3.client('s3')
            
            logger.info("S3 client initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            self.s3_client = None
    
    async def process_pdf(
        self, 
        s3_bucket: str, 
        s3_key: str, 
        user_id: str = "anonymous"
    ) -> Dict[str, Any]:
        """
        Process a PDF file: validate and convert to images if needed.
        Returns processing result with metadata.
        """
        try:
            if not self.s3_client:
                raise Exception("AWS S3 client not available")
            
            logger.info(f"Processing PDF: s3://{s3_bucket}/{s3_key}")
            
            # Download PDF from S3
            response = self.s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
            pdf_content = response['Body'].read()
            
            # Step 1: Try to extract text directly from PDF
            text_content = await self._extract_text_from_pdf(pdf_content)
            
            if text_content and len(text_content.strip()) > 50:
                # PDF has extractable text, use as-is
                logger.info(f"PDF has extractable text ({len(text_content)} characters), using as-is")
                
                # Upload to normalized documents bucket
                normalized_key = f"normalized-documents/{user_id}/{os.path.basename(s3_key)}"
                self.s3_client.put_object(
                    Bucket=s3_bucket,
                    Key=normalized_key,
                    Body=pdf_content,
                    ContentType='application/pdf'
                )
                
                return {
                    "status": "success",
                    "processing_type": "direct_pdf",
                    "text_length": len(text_content),
                    "normalized_key": normalized_key,
                    "message": "PDF processed directly - contains extractable text"
                }
            else:
                # PDF needs conversion to images
                logger.info("PDF has no extractable text, converting to images")
                return await self._convert_pdf_to_images(pdf_content, s3_bucket, s3_key, user_id)
                
        except Exception as e:
            logger.error(f"Error processing PDF {s3_key}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": f"Failed to process PDF: {e}"
            }
    
    async def _extract_text_from_pdf(self, pdf_content: bytes) -> Optional[str]:
        """
        Try to extract text from PDF using various libraries.
        """
        try:
            # Try PyPDF2 first
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                if text.strip():
                    logger.info("Successfully extracted text using PyPDF2")
                    return text
            except Exception as e:
                logger.debug(f"PyPDF2 extraction failed: {e}")
            
            # Try pdfminer.six
            try:
                from pdfminer.high_level import extract_text_to_fp
                from pdfminer.layout import LAParams
                
                output = io.StringIO()
                extract_text_to_fp(io.BytesIO(pdf_content), output, laparams=LAParams())
                text = output.getvalue()
                if text.strip():
                    logger.info("Successfully extracted text using pdfminer.six")
                    return text
            except Exception as e:
                logger.debug(f"pdfminer.six extraction failed: {e}")
            
            # Try PyMuPDF
            try:
                import fitz
                doc = fitz.open(stream=pdf_content, filetype="pdf")
                text = ""
                for page in doc:
                    text += page.get_text() + "\n"
                doc.close()
                if text.strip():
                    logger.info("Successfully extracted text using PyMuPDF")
                    return text
            except Exception as e:
                logger.debug(f"PyMuPDF extraction failed: {e}")
            
            return None
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return None
    
    async def _convert_pdf_to_images(
        self, 
        pdf_content: bytes, 
        s3_bucket: str, 
        original_key: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Convert PDF to images and upload to S3.
        """
        try:
            # Convert PDF to images using pdf2image
            image_files = await self._convert_pdf_to_images_local(pdf_content, original_key)
            
            if not image_files:
                raise Exception("Failed to convert PDF to images")
            
            # Upload images to S3
            uploaded_keys = []
            for i, (image_content, filename) in enumerate(image_files):
                s3_key = f"normalized-documents/{user_id}/images/{os.path.basename(original_key)}_page_{i+1}.png"
                
                self.s3_client.put_object(
                    Bucket=s3_bucket,
                    Key=s3_key,
                    Body=image_content,
                    ContentType='image/png'
                )
                uploaded_keys.append(s3_key)
                logger.info(f"Uploaded image {i+1}/{len(image_files)}: {s3_key}")
            
            return {
                "status": "success",
                "processing_type": "pdf_to_images",
                "image_count": len(image_files),
                "uploaded_keys": uploaded_keys,
                "message": f"PDF converted to {len(image_files)} images"
            }
            
        except Exception as e:
            logger.error(f"PDF to image conversion failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": f"Failed to convert PDF to images: {e}"
            }
    
    async def _convert_pdf_to_images_local(
        self, 
        pdf_content: bytes, 
        original_filename: str
    ) -> List[Tuple[bytes, str]]:
        """
        Convert PDF to images using pdf2image (requires poppler-utils).
        """
        try:
            # Try pdf2image first (requires poppler-utils)
            try:
                from pdf2image import convert_from_bytes
                
                images = convert_from_bytes(
                    pdf_content,
                    dpi=200,  # Good balance between quality and size
                    fmt='PNG',
                    thread_count=1
                )
                
                image_files = []
                for i, image in enumerate(images):
                    img_buffer = io.BytesIO()
                    image.save(img_buffer, format='PNG', optimize=True)
                    img_content = img_buffer.getvalue()
                    
                    filename = f"{original_filename}_page_{i+1}.png"
                    image_files.append((img_content, filename))
                
                logger.info(f"Successfully converted PDF to {len(image_files)} images using pdf2image")
                return image_files
                
            except ImportError:
                logger.warning("pdf2image not available, trying PyMuPDF")
            
            # Fallback to PyMuPDF
            try:
                import fitz
                
                doc = fitz.open(stream=pdf_content, filetype="pdf")
                image_files = []
                
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    
                    # Render page to image
                    mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Convert to PNG bytes
                    img_data = pix.tobytes("png")
                    
                    filename = f"{original_filename}_page_{page_num+1}.png"
                    image_files.append((img_data, filename))
                
                doc.close()
                logger.info(f"Successfully converted PDF to {len(image_files)} images using PyMuPDF")
                return image_files
                
            except ImportError:
                logger.error("Neither pdf2image nor PyMuPDF available")
                return []
            
        except Exception as e:
            logger.error(f"PDF to image conversion failed: {e}")
            return []

# Global instance
preprocessor = PDFPreprocessor()

# Example usage for testing
if __name__ == "__main__":
    import asyncio
    
    async def test_preprocessing():
        # Test with a sample PDF
        result = await preprocessor.process_pdf(
            s3_bucket="your-bucket-name",
            s3_key="test.pdf",
            user_id="test-user"
        )
        print(f"Processing result: {result}")
    
    asyncio.run(test_preprocessing()) 