"""
PDF Preprocessing Service for Visual Detection and Removal
Based on AWS Textract preprocessing techniques for better text extraction.
"""

import logging
import cv2
import numpy as np
import fitz  # PyMuPDF
from PIL import Image
import io
from typing import List, Tuple, Dict, Any
import asyncio

logger = logging.getLogger(__name__)

class PDFPreprocessingService:
    """PDF preprocessing service for visual detection and removal."""
    
    def __init__(self):
        """Initialize the preprocessing service."""
        self.opencv_params = {
            'min_width_percent': 0.1,  # Minimum width as percentage of page width
            'min_height_percent': 0.1,  # Minimum height as percentage of page height
            'padding_percent': 0.02,    # Extra padding around detected visuals
            'canny_low': 50,            # Canny edge detection low threshold
            'canny_high': 150           # Canny edge detection high threshold
        }
        
        self.pixel_analysis_params = {
            'non_text_horizontal_min': 0.1,   # Minimum black pixel concentration for non-text
            'non_text_horizontal_max': 0.8,   # Maximum black pixel concentration for non-text
            'non_text_vertical_min': 0.1,     # Minimum black pixel concentration for non-text
            'non_text_vertical_max': 0.8,     # Maximum black pixel concentration for non-text
            'window_size_x': 50,              # Horizontal window size in pixels
            'window_size_y': 50,              # Vertical window size in pixels
            'min_visual_area': 1000,          # Minimum area to be considered visual (pixels)
            'gray_range_threshold': 128       # Gray to white conversion threshold
        }
    
    async def preprocess_pdf_for_textract(self, file_content: bytes, filename: str) -> bytes:
        """
        Preprocess PDF to remove visuals and improve Textract performance.
        Returns processed PDF as bytes.
        """
        try:
            logger.info(f"Starting PDF preprocessing for {filename}")
            
            # Convert PDF to images
            pdf_images = await self._pdf_to_images(file_content)
            if not pdf_images:
                logger.warning(f"No pages found in PDF {filename}")
                return file_content
            
            processed_images = []
            
            for i, image in enumerate(pdf_images):
                logger.info(f"Processing page {i+1}/{len(pdf_images)}")
                
                # Try both preprocessing methods
                processed_image = await self._preprocess_page(image, i+1)
                processed_images.append(processed_image)
            
            # Convert processed images back to PDF
            processed_pdf = await self._images_to_pdf(processed_images, filename)
            
            logger.info(f"PDF preprocessing completed for {filename}")
            return processed_pdf
            
        except Exception as e:
            logger.error(f"Error preprocessing PDF {filename}: {e}")
            # Return original content if preprocessing fails
            return file_content
    
    async def _pdf_to_images(self, file_content: bytes) -> List[np.ndarray]:
        """Convert PDF to list of images."""
        try:
            pdf_document = fitz.open(stream=file_content, filetype="pdf")
            images = []
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Get page matrix for rendering
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                pil_image = Image.open(io.BytesIO(img_data))
                
                # Convert to OpenCV format
                opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                images.append(opencv_image)
            
            pdf_document.close()
            return images
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")
            return []
    
    async def _preprocess_page(self, image: np.ndarray, page_num: int) -> np.ndarray:
        """Preprocess a single page using both methods."""
        try:
            # Method 1: OpenCV Edge Detection
            edge_processed = await self._opencv_edge_detection(image, page_num)
            
            # Method 2: Pixel Concentration Analysis
            pixel_processed = await self._pixel_concentration_analysis(image, page_num)
            
            # Combine results - use the method that removes more visuals
            edge_visual_ratio = self._calculate_visual_ratio(image, edge_processed)
            pixel_visual_ratio = self._calculate_visual_ratio(image, pixel_processed)
            
            if edge_visual_ratio > pixel_visual_ratio:
                logger.info(f"Page {page_num}: Using OpenCV edge detection (removed {edge_visual_ratio:.2%} visuals)")
                return edge_processed
            else:
                logger.info(f"Page {page_num}: Using pixel concentration analysis (removed {pixel_visual_ratio:.2%} visuals)")
                return pixel_processed
                
        except Exception as e:
            logger.error(f"Error preprocessing page {page_num}: {e}")
            return image
    
    async def _opencv_edge_detection(self, image: np.ndarray, page_num: int) -> np.ndarray:
        """Method 1: OpenCV Canny Edge Detection for visual removal."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply Canny edge detection
            edges = cv2.Canny(blurred, 
                            self.opencv_params['canny_low'], 
                            self.opencv_params['canny_high'])
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Create mask for visuals
            mask = np.ones_like(gray) * 255
            height, width = gray.shape
            
            min_width = int(width * self.opencv_params['min_width_percent'])
            min_height = int(height * self.opencv_params['min_height_percent'])
            padding = int(min(min_width, min_height) * self.opencv_params['padding_percent'])
            
            for contour in contours:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Check if contour meets minimum size requirements
                if w >= min_width and h >= min_height:
                    # Add padding
                    x_start = max(0, x - padding)
                    y_start = max(0, y - padding)
                    x_end = min(width, x + w + padding)
                    y_end = min(height, y + h + padding)
                    
                    # Fill the area with white
                    mask[y_start:y_end, x_start:x_end] = 255
            
            # Apply mask to original image
            result = cv2.bitwise_and(image, image, mask=mask)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in OpenCV edge detection for page {page_num}: {e}")
            return image
    
    async def _pixel_concentration_analysis(self, image: np.ndarray, page_num: int) -> np.ndarray:
        """Method 2: Pixel Concentration Analysis for visual removal."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Convert gray areas to white
            _, binary = cv2.threshold(gray, self.pixel_analysis_params['gray_range_threshold'], 255, cv2.THRESH_BINARY)
            
            height, width = binary.shape
            result = image.copy()
            
            # Analyze horizontal segments
            y_window = self.pixel_analysis_params['window_size_y']
            x_window = self.pixel_analysis_params['window_size_x']
            
            for y in range(0, height, y_window):
                y_end = min(y + y_window, height)
                
                # Calculate horizontal pixel concentration
                horizontal_concentration = np.sum(binary[y:y_end, :] == 0) / (width * (y_end - y))
                
                # Check if this segment is non-text (visual)
                if (self.pixel_analysis_params['non_text_horizontal_min'] <= 
                    horizontal_concentration <= 
                    self.pixel_analysis_params['non_text_horizontal_max']):
                    
                    # Analyze vertical segments within this horizontal segment
                    for x in range(0, width, x_window):
                        x_end = min(x + x_window, width)
                        
                        # Calculate vertical pixel concentration
                        vertical_concentration = np.sum(binary[y:y_end, x:x_end] == 0) / ((x_end - x) * (y_end - y))
                        
                        # Check if this area is non-text (visual)
                        if (self.pixel_analysis_params['non_text_vertical_min'] <= 
                            vertical_concentration <= 
                            self.pixel_analysis_params['non_text_vertical_max']):
                            
                            area = (x_end - x) * (y_end - y)
                            if area >= self.pixel_analysis_params['min_visual_area']:
                                # Fill with white
                                result[y:y_end, x:x_end] = [255, 255, 255]
            
            return result
            
        except Exception as e:
            logger.error(f"Error in pixel concentration analysis for page {page_num}: {e}")
            return image
    
    def _calculate_visual_ratio(self, original: np.ndarray, processed: np.ndarray) -> float:
        """Calculate the ratio of visual area removed."""
        try:
            # Convert to grayscale for comparison
            orig_gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
            proc_gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
            
            # Count white pixels (removed content)
            orig_white = np.sum(orig_gray == 255)
            proc_white = np.sum(proc_gray == 255)
            
            total_pixels = orig_gray.size
            
            # Calculate ratio of additional white pixels (removed visuals)
            removed_ratio = (proc_white - orig_white) / total_pixels
            
            return max(0, removed_ratio)
            
        except Exception as e:
            logger.error(f"Error calculating visual ratio: {e}")
            return 0.0
    
    async def _images_to_pdf(self, images: List[np.ndarray], filename: str) -> bytes:
        """Convert processed images back to PDF."""
        try:
            # Create a new PDF document
            pdf_document = fitz.open()
            
            for i, image in enumerate(images):
                # Convert OpenCV image to PIL
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(image_rgb)
                
                # Convert PIL image to bytes
                img_bytes = io.BytesIO()
                pil_image.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                
                # Create PDF page
                page = pdf_document.new_page()
                
                # Insert image into page
                page.insert_image(page.rect, stream=img_bytes.getvalue())
            
            # Save PDF to bytes
            pdf_bytes = pdf_document.write()
            pdf_document.close()
            
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error converting images to PDF: {e}")
            raise
    
    def get_preprocessing_stats(self, original_size: int, processed_size: int) -> Dict[str, Any]:
        """Get preprocessing statistics."""
        return {
            "original_size_bytes": original_size,
            "processed_size_bytes": processed_size,
            "size_reduction_percent": ((original_size - processed_size) / original_size) * 100 if original_size > 0 else 0,
            "preprocessing_method": "OpenCV Edge Detection + Pixel Concentration Analysis"
        }

# Global instance
pdf_preprocessing_service = PDFPreprocessingService() 