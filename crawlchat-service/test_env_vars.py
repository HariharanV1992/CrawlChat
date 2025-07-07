#!/usr/bin/env python3
"""
Test script to verify environment variable loading
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_environment_variables():
    """Test environment variable loading."""
    logger.info("🔧 Testing Environment Variable Loading")
    logger.info("=" * 50)
    
    # Test direct environment variable access
    logger.info("📋 Direct Environment Variable Access:")
    openai_key_direct = os.environ.get('OPENAI_API_KEY')
    logger.info(f"   OPENAI_API_KEY: {'✅ Set' if openai_key_direct else '❌ Not found'}")
    
    if openai_key_direct:
        logger.info(f"   Key length: {len(openai_key_direct)} characters")
        logger.info(f"   Key starts with: {openai_key_direct[:10]}...")
    
    # Test configuration system
    logger.info("\n📋 Configuration System Access:")
    try:
        from common.src.core.config import config
        openai_key_config = config.openai_api_key
        logger.info(f"   Config.openai_api_key: {'✅ Set' if openai_key_config else '❌ Not found'}")
        
        if openai_key_config:
            logger.info(f"   Key length: {len(openai_key_config)} characters")
            logger.info(f"   Key starts with: {openai_key_config[:10]}...")
        
        # Test other config values
        logger.info(f"   Config.openai_model: {config.openai_model}")
        logger.info(f"   Config.openai_max_tokens: {config.openai_max_tokens}")
        logger.info(f"   Config.openai_temperature: {config.openai_temperature}")
        
    except Exception as e:
        logger.error(f"   ❌ Error loading config: {e}")
    
    # Test alternative environment variable names
    logger.info("\n📋 Alternative Environment Variable Names:")
    alt_names = ['openai_api_key', 'OPENAI_API_KEY', 'OpenAI_API_Key']
    for name in alt_names:
        value = os.environ.get(name)
        logger.info(f"   {name}: {'✅ Set' if value else '❌ Not found'}")
    
    # Test OpenAI client initialization
    logger.info("\n📋 OpenAI Client Initialization Test:")
    try:
        from openai import OpenAI
        
        # Try with direct environment variable
        if openai_key_direct:
            client_direct = OpenAI(api_key=openai_key_direct)
            logger.info("   ✅ OpenAI client created with direct env var")
        else:
            logger.warning("   ⚠️ Cannot test OpenAI client - no API key")
            
        # Try with config
        if 'openai_key_config' in locals() and openai_key_config:
            client_config = OpenAI(api_key=openai_key_config)
            logger.info("   ✅ OpenAI client created with config")
            
    except Exception as e:
        logger.error(f"   ❌ Error creating OpenAI client: {e}")
    
    # Environment information
    logger.info("\n📋 Environment Information:")
    logger.info(f"   Python version: {sys.version}")
    logger.info(f"   Working directory: {os.getcwd()}")
    logger.info(f"   Lambda environment: {'Yes' if os.environ.get('AWS_LAMBDA_FUNCTION_NAME') else 'No'}")
    
    # List all environment variables containing 'OPENAI'
    logger.info("\n📋 All OpenAI-related Environment Variables:")
    openai_vars = {k: v for k, v in os.environ.items() if 'OPENAI' in k.upper()}
    if openai_vars:
        for key, value in openai_vars.items():
            masked_value = value[:10] + "..." if len(value) > 10 else value
            logger.info(f"   {key}: {masked_value}")
    else:
        logger.warning("   No OpenAI-related environment variables found")

def test_vector_store_initialization():
    """Test vector store service initialization."""
    logger.info("\n🔧 Testing Vector Store Service Initialization")
    logger.info("=" * 50)
    
    try:
        from common.src.services.vector_store_service import VectorStoreService
        
        # This should trigger the _initialize_openai_client method
        vector_store = VectorStoreService()
        logger.info("   ✅ VectorStoreService initialized successfully")
        
        # Test if client was created
        if hasattr(vector_store, 'client') and vector_store.client:
            logger.info("   ✅ OpenAI client created successfully")
        else:
            logger.error("   ❌ OpenAI client not created")
            
    except Exception as e:
        logger.error(f"   ❌ Error initializing VectorStoreService: {e}")

def main():
    """Run all tests."""
    logger.info("🚀 Starting Environment Variable Tests")
    logger.info("=" * 60)
    
    test_environment_variables()
    test_vector_store_initialization()
    
    logger.info("\n✅ Environment variable tests completed")

if __name__ == "__main__":
    main() 