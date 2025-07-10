# Local Lambda Deployment Guide

This guide explains how to deploy and test the CrawlChat Lambda functions locally using Docker containers.

## Prerequisites

- Docker installed and running
- Python 3.8+ (for testing)
- Required environment variables (optional for basic testing)

## Quick Start

### 1. Deploy Lambda Functions Locally

```bash
# Deploy both Lambda functions
./deploy_local.sh

# Or explicitly specify deploy command
./deploy_local.sh deploy
```

This will:
- Build Docker images for both Lambda functions
- Start containers on ports 9000 (Lambda API) and 9001 (Crawler)
- Run health checks
- Display service URLs and useful commands

### 2. Test the Functions

```bash
# Run comprehensive tests
python3 test_local_lambdas.py
```

### 3. View Logs and Status

```bash
# Show container status
./deploy_local.sh status

# View Lambda API logs
./deploy_local.sh logs crawlchat-lambda-api-local

# View Crawler logs
./deploy_local.sh logs crawlchat-crawler-local
```

### 4. Clean Up

```bash
# Stop and remove containers and images
./deploy_local.sh cleanup
```

## Service URLs

After deployment, the services will be available at:

- **Lambda API**: http://localhost:9000
- **Crawler**: http://localhost:9001

## Environment Variables

You can set these environment variables before running the deployment:

```bash
export MONGODB_URI="your_mongodb_connection_string"
export DB_NAME="stock_market_crawler"
export SCRAPINGBEE_API_KEY="your_scrapingbee_api_key"
```

## Testing Endpoints

### Lambda API Endpoints

- `GET /health` - Health check
- `GET /api/v1/auth/verify` - Auth verification
- `GET /api/v1/chat/sessions` - Chat sessions
- `GET /api/v1/crawler/health` - Crawler health (via API)

### Crawler Endpoints

- `GET /health` - Health check
- `POST /tasks` - Create crawl task
- `GET /tasks/{task_id}` - Get task status
- `POST /tasks/{task_id}/start` - Start crawl task

### Direct Lambda Invocation

Both functions support direct Lambda invocation format:

```bash
# Lambda API
curl -X POST http://localhost:9000/ \
  -H "Content-Type: application/json" \
  -d '{"httpMethod": "GET", "path": "/health"}'

# Crawler
curl -X POST http://localhost:9001/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "max_doc_count": 1}'
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Check what's using the ports
   lsof -i :9000
   lsof -i :9001
   
   # Kill processes if needed
   sudo kill -9 <PID>
   ```

2. **Docker build fails**
   ```bash
   # Check Docker daemon is running
   docker ps
   
   # Clean up Docker cache
   docker system prune -a
   ```

3. **Containers not starting**
   ```bash
   # Check container logs
   ./deploy_local.sh logs crawlchat-lambda-api-local
   ./deploy_local.sh logs crawlchat-crawler-local
   
   # Check Docker resources
   docker stats
   ```

### Debug Mode

For debugging, you can run containers in interactive mode:

```bash
# Stop existing containers
./deploy_local.sh cleanup

# Run Lambda API in interactive mode
docker run -it --rm \
  -p 9000:8080 \
  -e AWS_REGION=ap-south-1 \
  crawlchat-lambda-api:local

# Run Crawler in interactive mode
docker run -it --rm \
  -p 9001:8080 \
  -e AWS_REGION=ap-south-1 \
  crawlchat-crawler:local
```

## Development Workflow

1. **Make changes to code**
2. **Rebuild and redeploy**
   ```bash
   ./deploy_local.sh cleanup
   ./deploy_local.sh deploy
   ```
3. **Test changes**
   ```bash
   python3 test_local_lambdas.py
   ```
4. **View logs for debugging**
   ```bash
   ./deploy_local.sh logs crawlchat-lambda-api-local
   ```

## Integration with UI

The local Lambda functions can be integrated with the existing UI by updating the API endpoints in the frontend configuration to point to the local URLs.

## Performance Testing

For performance testing, you can use tools like Apache Bench:

```bash
# Test Lambda API performance
ab -n 100 -c 10 http://localhost:9000/health

# Test Crawler performance
ab -n 50 -c 5 -p test_payload.json -T application/json http://localhost:9001/tasks
```

## Monitoring

Monitor the containers using:

```bash
# Real-time container stats
docker stats

# Container resource usage
docker system df

# Container logs in real-time
docker logs -f crawlchat-lambda-api-local
docker logs -f crawlchat-crawler-local
```

## Security Notes

- The local deployment is for development/testing only
- No production secrets should be used
- Containers run with minimal security restrictions
- Use environment variables for sensitive data

## Next Steps

After successful local testing:

1. **Deploy to AWS** using the GitHub Actions workflow
2. **Update production environment variables**
3. **Monitor production logs**
4. **Scale resources as needed**

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review container logs
3. Verify environment variables
4. Ensure Docker has sufficient resources
5. Check network connectivity for external services 