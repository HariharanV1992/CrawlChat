#!/usr/bin/env python3
"""
Local Lambda Deployment Script for CrawlChat

This script deploys both Lambda functions locally using Docker containers
for testing before AWS deployment.
"""

import os
import sys
import subprocess
import json
import time
import requests
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LocalLambdaDeployer:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.crawlchat_dir = self.base_dir / "crawlchat-service"
        self.lambda_service_dir = self.crawlchat_dir / "lambda-service"
        self.crawler_service_dir = self.crawlchat_dir / "crawler-service"
        
        # Ports for local Lambda functions
        self.lambda_api_port = 9000
        self.crawler_port = 9001
        
        # Container names
        self.lambda_api_container = "crawlchat-lambda-api-local"
        self.crawler_container = "crawlchat-crawler-local"
        
        # Environment variables
        self.env_vars = {
            "AWS_REGION": "ap-south-1",
            "LAMBDA_FUNCTION_NAME": "crawlchat-api-function",
            "CRAWLER_FUNCTION_NAME": "crawlchat-crawler-function",
            "STACK_NAME": "crawlchat-stack",
            "MONGODB_URI": os.getenv("MONGODB_URI", ""),
            "DB_NAME": os.getenv("DB_NAME", "stock_market_crawler"),
            "SCRAPINGBEE_API_KEY": os.getenv("SCRAPINGBEE_API_KEY", ""),
            "CRAWLCHAT_SQS_QUEUE": "crawlchat-crawl-tasks"
        }

    def check_prerequisites(self):
        """Check if Docker and required tools are available."""
        logger.info("🔍 Checking prerequisites...")
        
        # Check Docker
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Docker found: {result.stdout.strip()}")
            else:
                logger.error("❌ Docker not found or not working")
                return False
        except FileNotFoundError:
            logger.error("❌ Docker not installed")
            return False
        
        # Check if directories exist
        if not self.lambda_service_dir.exists():
            logger.error(f"❌ Lambda service directory not found: {self.lambda_service_dir}")
            return False
        
        if not self.crawler_service_dir.exists():
            logger.error(f"❌ Crawler service directory not found: {self.crawler_service_dir}")
            return False
        
        logger.info("✅ All prerequisites met")
        return True

    def build_lambda_api_image(self):
        """Build the Lambda API Docker image."""
        logger.info("🔨 Building Lambda API Docker image...")
        
        dockerfile_path = self.lambda_service_dir / "Dockerfile"
        if not dockerfile_path.exists():
            logger.error(f"❌ Dockerfile not found: {dockerfile_path}")
            return False
        
        try:
            cmd = [
                "docker", "build",
                "-t", "crawlchat-lambda-api:local",
                "-f", str(dockerfile_path),
                str(self.lambda_service_dir)
            ]
            
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Lambda API image built successfully")
                return True
            else:
                logger.error(f"❌ Failed to build Lambda API image: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error building Lambda API image: {e}")
            return False

    def build_crawler_image(self):
        """Build the Crawler Docker image."""
        logger.info("🔨 Building Crawler Docker image...")
        
        dockerfile_path = self.crawler_service_dir / "Dockerfile"
        if not dockerfile_path.exists():
            logger.error(f"❌ Dockerfile not found: {dockerfile_path}")
            return False
        
        try:
            cmd = [
                "docker", "build",
                "-t", "crawlchat-crawler:local",
                "-f", str(dockerfile_path),
                str(self.crawler_service_dir)
            ]
            
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Crawler image built successfully")
                return True
            else:
                logger.error(f"❌ Failed to build Crawler image: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error building Crawler image: {e}")
            return False

    def stop_existing_containers(self):
        """Stop any existing containers."""
        logger.info("🛑 Stopping existing containers...")
        
        containers = [self.lambda_api_container, self.crawler_container]
        
        for container in containers:
            try:
                # Stop container if running
                subprocess.run(["docker", "stop", container], capture_output=True)
                logger.info(f"✅ Stopped container: {container}")
            except:
                pass
            
            try:
                # Remove container if exists
                subprocess.run(["docker", "rm", container], capture_output=True)
                logger.info(f"✅ Removed container: {container}")
            except:
                pass

    def run_lambda_api_container(self):
        """Run the Lambda API container."""
        logger.info(f"🚀 Starting Lambda API container on port {self.lambda_api_port}...")
        
        env_vars = []
        for key, value in self.env_vars.items():
            env_vars.extend(["-e", f"{key}={value}"])
        
        try:
            cmd = [
                "docker", "run",
                "-d",
                "--name", self.lambda_api_container,
                "-p", f"{self.lambda_api_port}:8080",
                "--env-file", str(self.lambda_service_dir / ".env") if (self.lambda_service_dir / ".env").exists() else None,
                *env_vars,
                "crawlchat-lambda-api:local"
            ]
            
            # Remove None values
            cmd = [arg for arg in cmd if arg is not None]
            
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Lambda API container started: {result.stdout.strip()}")
                return True
            else:
                logger.error(f"❌ Failed to start Lambda API container: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting Lambda API container: {e}")
            return False

    def run_crawler_container(self):
        """Run the Crawler container."""
        logger.info(f"🚀 Starting Crawler container on port {self.crawler_port}...")
        
        env_vars = []
        for key, value in self.env_vars.items():
            env_vars.extend(["-e", f"{key}={value}"])
        
        try:
            cmd = [
                "docker", "run",
                "-d",
                "--name", self.crawler_container,
                "-p", f"{self.crawler_port}:8080",
                "--env-file", str(self.crawler_service_dir / ".env") if (self.crawler_service_dir / ".env").exists() else None,
                *env_vars,
                "crawlchat-crawler:local"
            ]
            
            # Remove None values
            cmd = [arg for arg in cmd if arg is not None]
            
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Crawler container started: {result.stdout.strip()}")
                return True
            else:
                logger.error(f"❌ Failed to start Crawler container: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting Crawler container: {e}")
            return False

    def wait_for_containers(self, timeout=60):
        """Wait for containers to be ready."""
        logger.info("⏳ Waiting for containers to be ready...")
        
        start_time = time.time()
        containers_ready = {"lambda_api": False, "crawler": False}
        
        while time.time() - start_time < timeout:
            # Check Lambda API
            if not containers_ready["lambda_api"]:
                try:
                    response = requests.get(f"http://localhost:{self.lambda_api_port}/health", timeout=5)
                    if response.status_code == 200:
                        logger.info("✅ Lambda API container is ready")
                        containers_ready["lambda_api"] = True
                except:
                    pass
            
            # Check Crawler
            if not containers_ready["crawler"]:
                try:
                    response = requests.get(f"http://localhost:{self.crawler_port}/health", timeout=5)
                    if response.status_code == 200:
                        logger.info("✅ Crawler container is ready")
                        containers_ready["crawler"] = True
                except:
                    pass
            
            if all(containers_ready.values()):
                logger.info("✅ All containers are ready!")
                return True
            
            time.sleep(2)
        
        logger.error("❌ Timeout waiting for containers to be ready")
        return False

    def test_lambda_api(self):
        """Test the Lambda API function."""
        logger.info("🧪 Testing Lambda API function...")
        
        try:
            # Test health endpoint
            response = requests.get(f"http://localhost:{self.lambda_api_port}/health")
            logger.info(f"Health endpoint: {response.status_code} - {response.text}")
            
            # Test crawler endpoints
            response = requests.get(f"http://localhost:{self.lambda_api_port}/api/v1/crawler/health")
            logger.info(f"Crawler health: {response.status_code} - {response.text}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error testing Lambda API: {e}")
            return False

    def test_crawler(self):
        """Test the Crawler function."""
        logger.info("🧪 Testing Crawler function...")
        
        try:
            # Test health endpoint
            response = requests.get(f"http://localhost:{self.crawler_port}/health")
            logger.info(f"Health endpoint: {response.status_code} - {response.text}")
            
            # Test task creation
            task_data = {
                "url": "https://example.com",
                "max_doc_count": 1
            }
            response = requests.post(f"http://localhost:{self.crawler_port}/tasks", json=task_data)
            logger.info(f"Task creation: {response.status_code} - {response.text}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error testing Crawler: {e}")
            return False

    def show_status(self):
        """Show the status of running containers."""
        logger.info("📊 Container Status:")
        
        try:
            result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(result.stdout)
            else:
                logger.error("Failed to get container status")
        except Exception as e:
            logger.error(f"Error getting container status: {e}")

    def show_logs(self, container_name):
        """Show logs for a specific container."""
        logger.info(f"📋 Logs for {container_name}:")
        
        try:
            result = subprocess.run(["docker", "logs", container_name], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(result.stdout)
            else:
                logger.error(f"Failed to get logs for {container_name}")
        except Exception as e:
            logger.error(f"Error getting logs for {container_name}: {e}")

    def deploy(self):
        """Deploy all Lambda functions locally."""
        logger.info("🚀 Starting local Lambda deployment...")
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        # Stop existing containers
        self.stop_existing_containers()
        
        # Build images
        if not self.build_lambda_api_image():
            return False
        
        if not self.build_crawler_image():
            return False
        
        # Run containers
        if not self.run_lambda_api_container():
            return False
        
        if not self.run_crawler_container():
            return False
        
        # Wait for containers to be ready
        if not self.wait_for_containers():
            return False
        
        # Test functions
        self.test_lambda_api()
        self.test_crawler()
        
        # Show status
        self.show_status()
        
        logger.info("🎉 Local Lambda deployment completed!")
        logger.info(f"📋 Lambda API: http://localhost:{self.lambda_api_port}")
        logger.info(f"📋 Crawler: http://localhost:{self.crawler_port}")
        
        return True

    def cleanup(self):
        """Clean up containers and images."""
        logger.info("🧹 Cleaning up...")
        
        # Stop and remove containers
        self.stop_existing_containers()
        
        # Remove images
        try:
            subprocess.run(["docker", "rmi", "crawlchat-lambda-api:local"], capture_output=True)
            subprocess.run(["docker", "rmi", "crawlchat-crawler:local"], capture_output=True)
            logger.info("✅ Images removed")
        except:
            pass

def main():
    """Main function."""
    deployer = LocalLambdaDeployer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "deploy":
            deployer.deploy()
        elif command == "cleanup":
            deployer.cleanup()
        elif command == "status":
            deployer.show_status()
        elif command == "logs":
            if len(sys.argv) > 2:
                container = sys.argv[2]
                deployer.show_logs(container)
            else:
                logger.error("Please specify container name: logs <container_name>")
        else:
            logger.error(f"Unknown command: {command}")
            logger.info("Available commands: deploy, cleanup, status, logs")
    else:
        # Default: deploy
        deployer.deploy()

if __name__ == "__main__":
    main() 