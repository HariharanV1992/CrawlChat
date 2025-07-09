from core.config import config
from core.database import mongodb
from core.logging import setup_logging
from api.v1.auth import router as auth_router
from api.v1.chat import router as chat_router
from api.v1.crawler import router as crawler_router
from api.v1.documents import router as documents_router
from api.v1.vector_store import router as vector_store_router
from api.v1.preprocessing import router as preprocessing_router 