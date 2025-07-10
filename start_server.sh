#!/bin/bash

# Start Local CrawlChat Test Server
echo "🚀 Starting CrawlChat Local Test Server..."

# Kill any existing processes
echo "🔄 Stopping any existing servers..."
pkill -f "uvicorn" 2>/dev/null
pkill -f "test_crawler_server.py" 2>/dev/null
sleep 2

# Set the API key
export SCRAPINGBEE_API_KEY="NV9KS7HERG9249QDV83S4FXJS8732HVO79JM6Y3O9X4W4OBNMQKHI3F8VP7HBGF0JGSS4PT47QLRFUX6"

# Start the server
echo "🌟 Starting server on http://localhost:8000"
echo "📋 Available endpoints:"
echo "   - Health: http://localhost:8000/health"
echo "   - Crawler UI: http://localhost:8000/crawler"
echo "   - Chat UI: http://localhost:8000/chat"
echo "   - Login UI: http://localhost:8000/login"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Change to the correct directory and start
cd crawlchat-service && python3 test_crawler_server.py 