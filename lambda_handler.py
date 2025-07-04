"""
Lambda handler for FastAPI application using Mangum.
"""

from mangum import Mangum
from main import app

handler = Mangum(app) 