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
    ],
    python_requires=">=3.8",
) 