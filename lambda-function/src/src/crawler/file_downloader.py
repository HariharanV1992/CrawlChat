"""
File downloader for the enhanced stock market crawler.
"""

import os
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import mimetypes

logger = logging.getLogger(__name__)

class FileDownloader:
    """Handles file download logic for documents, PDFs, etc."""
    def __init__(self, output_dir: str, min_file_size: int = 1000):
        self.output_dir = Path(output_dir)
        self.min_file_size = min_file_size
        self.downloaded_files = []
        self.failed_downloads = []
        self.total_downloaded_size = 0
        self.documents_downloaded = 0
        self.document_extensions = ['.pdf', '.doc', '.docx', '.xlsx', '.xls', '.ppt', '.pptx', '.csv', '.json']
    
    def is_document_url(self, url: str) -> bool:
        """Check if URL points to a document."""
        return any(ext in url.lower() for ext in self.document_extensions)
    
    def get_filename_from_url(self, url: str) -> str:
        """Extract filename from URL."""
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        if not filename or '.' not in filename:
            # Generate filename based on content type
            content_type, _ = mimetypes.guess_type(url)
            if content_type:
                ext = mimetypes.guess_extension(content_type)
                filename = f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext or '.bin'}"
            else:
                filename = f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bin"
        return filename
    
    def is_valid_document(self, file_info: Dict[str, Any]) -> bool:
        if file_info['size'] < self.min_file_size:
            logger.debug(f"Skipping small file: {file_info['filename']} ({file_info['size']} bytes) - below minimum size {self.min_file_size}")
            return False
        return True
    
    def save_file(self, file_path: Path, content: bytes):
        """Save file content to disk."""
        file_path.parent.mkdir(exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(content)
        logger.info(f"Saved file: {file_path}")
    
    def download_document(self, url: str, proxy_manager, timeout: int = 30) -> bool:
        """Download a document from URL."""
        try:
            logger.info(f"Downloading document: {url}")
            response = proxy_manager.make_request(url, is_binary=True, timeout=timeout)
            
            if response.status_code != 200:
                logger.warning(f"Failed to download {url}: HTTP {response.status_code}")
                self.record_failure(url, f"HTTP {response.status_code}")
                return False
            
            content = response.content
            if len(content) < self.min_file_size:
                logger.debug(f"Document too small: {url} ({len(content)} bytes)")
                return False
            
            filename = self.get_filename_from_url(url)
            file_path = self.output_dir / filename
            
            # Ensure unique filename
            counter = 1
            original_path = file_path
            while file_path.exists():
                stem = original_path.stem
                suffix = original_path.suffix
                file_path = self.output_dir / f"{stem}_{counter}{suffix}"
                counter += 1
            
            self.save_file(file_path, content)
            self.record_download(url, filename, len(content), self.get_file_type(url))
            return True
            
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            self.record_failure(url, str(e))
            return False
    
    def get_file_type(self, url: str) -> str:
        """Get file type from URL."""
        for ext in self.document_extensions:
            if ext in url.lower():
                return ext[1:].upper()  # Remove dot and uppercase
        return "UNKNOWN"
    
    def record_download(self, url: str, filename: str, size: int, file_type: str):
        self.downloaded_files.append({
            'url': url,
            'filename': filename,
            'size': size,
            'type': file_type,
            'timestamp': datetime.now().isoformat()
        })
        self.total_downloaded_size += size
        self.documents_downloaded += 1
    
    def record_failure(self, url: str, error: str):
        self.failed_downloads.append({
            'url': url,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_stats(self):
        return {
            'files_downloaded': len(self.downloaded_files),
            'failed_downloads': len(self.failed_downloads),
            'total_downloaded_size': self.total_downloaded_size,
            'documents_downloaded': self.documents_downloaded
        } 