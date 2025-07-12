from setuptools import setup, find_packages

setup(
    name="crawlchat-common",
    version="1.0.0",
    description="Common package for CrawlChat services",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "motor>=3.0.0",
        "pymongo>=4.0.0",
        "boto3>=1.26.0",
        "botocore>=1.29.0",
        "python-multipart>=0.0.6",
        # Document processing dependencies
        "PyPDF2>=3.0.0",
        "pdfminer.six>=20221105",
        "pdf2image>=1.16.0",
        "Pillow>=10.0.0",
        "Pillow-SIMD>=9.5.0",
        "openpyxl>=3.1.0",
        "python-docx>=1.1.0",
        "python-pptx>=0.6.21",
        "html2text>=2020.1.16",
        "python-dateutil>=2.8.2",
    ],
    python_requires=">=3.8",
) 