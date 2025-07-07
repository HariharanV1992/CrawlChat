# How CrawlChat Works - Simple Guide

## What You Have

**3 Services in AWS:**

1. **API Service** (Lambda) - Main website backend
2. **Crawler Service** (Lambda) - Web scraping robot  
3. **Preprocessor Service** (ECS) - PDF converter

## How It Works

```
User → API Service → Crawler/Preprocessor → Response
```

## Current Status

✅ **Working:** API Service (crawlchat.site works)
❌ **Missing:** Crawler & Preprocessor functions

## To Complete

Run these scripts:
```bash
./create_crawler_function.sh
./create_preprocessor_service.sh
```

## Cost

- **Lambda:** Pay per request (~$0.20/million)
- **ECS:** Pay per hour (~$10-20/month)
- **ECR:** Pay per GB (~$0.10/GB/month)

## Why This Setup?

- **Lambda:** Good for occasional tasks (API, crawling)
- **ECS:** Good for continuous tasks (PDF processing)
- **ECR:** Stores your application packages 