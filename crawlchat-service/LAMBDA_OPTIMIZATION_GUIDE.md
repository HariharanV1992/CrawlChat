# Lambda Optimization Guide

## 🚀 **Current Issues & Solutions**

### **Issue 1: Cold Start Timeout (10+ seconds)**
**Problem**: Lambda initialization is taking too long, causing timeouts.

**Solutions**:

#### 1. **Increase Lambda Memory**
```bash
# Update Lambda memory allocation
aws lambda update-function-configuration \
  --function-name crawlchat-api-function \
  --memory-size 2048 \
  --timeout 30 \
  --region ap-south-1
```

#### 2. **Enable Provisioned Concurrency**
```bash
# Create provisioned concurrency
aws lambda put-provisioned-concurrency-config \
  --function-name crawlchat-api-function \
  --qualifier \$LATEST \
  --provisioned-concurrent-executions 1 \
  --region ap-south-1
```

#### 3. **Optimize Dependencies**
- Remove unused packages from `requirements.txt`
- Use Lambda layers for common dependencies
- Lazy load heavy modules

### **Issue 2: Authentication Failures**
**Status**: ✅ **FIXED** - Authentication is working correctly
- **Correct credentials**: `harito2do@gmail.com` / `password123`
- **Test script**: `test_auth_fix.py` confirms it's working

## 🔧 **Lambda Configuration Recommendations**

### **Memory & Timeout Settings**
```json
{
  "MemorySize": 2048,
  "Timeout": 30,
  "ReservedConcurrencyLimit": 10
}
```

### **Environment Variables**
```bash
# Required for optimal performance
PYTHONPATH=/var/task
AWS_LAMBDA_FUNCTION_NAME=crawlchat-api-function
AWS_LAMBDA_FUNCTION_MEMORY_SIZE=2048
AWS_LAMBDA_FUNCTION_VERSION=\$LATEST
```

## 📊 **Performance Monitoring**

### **CloudWatch Metrics to Monitor**
- **Duration**: Should be < 5 seconds for most requests
- **Memory Used**: Should be < 80% of allocated memory
- **Cold Start Count**: Should decrease with provisioned concurrency
- **Error Rate**: Should be < 1%

### **Log Analysis Commands**
```bash
# Monitor Lambda logs in real-time
aws logs tail /aws/lambda/crawlchat-api-function --follow

# Check recent errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/crawlchat-api-function \
  --filter-pattern "ERROR" \
  --start-time $(date -d '1 hour ago' +%s)000

# Check cold start times
aws logs filter-log-events \
  --log-group-name /aws/lambda/crawlchat-api-function \
  --filter-pattern "INIT_REPORT" \
  --start-time $(date -d '1 hour ago' +%s)000
```

## 🎯 **Immediate Actions**

### **1. Update Lambda Configuration**
```bash
# Run these commands to optimize Lambda
aws lambda update-function-configuration \
  --function-name crawlchat-api-function \
  --memory-size 2048 \
  --timeout 30 \
  --region ap-south-1

aws lambda update-function-configuration \
  --function-name crawlchat-crawler-function \
  --memory-size 1024 \
  --timeout 60 \
  --region ap-south-1
```

### **2. Test Authentication**
```bash
# Run the authentication test
python test_auth_fix.py
```

### **3. Monitor Performance**
```bash
# Check Lambda function status
aws lambda get-function --function-name crawlchat-api-function

# Monitor logs
aws logs tail /aws/lambda/crawlchat-api-function --follow
```

## 🔍 **Troubleshooting**

### **If Cold Starts Persist**
1. **Check dependency size**: Large packages increase cold start time
2. **Use Lambda layers**: Move common dependencies to layers
3. **Enable provisioned concurrency**: Keeps functions warm
4. **Optimize imports**: Lazy load heavy modules

### **If Authentication Still Fails**
1. **Verify user exists**: Run `python create_default_user.py`
2. **Check password**: Use `password123` for testing
3. **Test locally**: Run `python test_auth_fix.py`
4. **Check MongoDB connection**: Ensure database is accessible

### **If Memory Issues Occur**
1. **Increase memory allocation**: More memory = faster execution
2. **Monitor memory usage**: Check CloudWatch metrics
3. **Optimize code**: Reduce memory footprint
4. **Use streaming**: For large file processing

## 📈 **Expected Performance After Optimization**

### **Cold Start Times**
- **Without optimization**: 8-10 seconds
- **With 2048MB memory**: 3-5 seconds
- **With provisioned concurrency**: < 1 second

### **Warm Request Times**
- **Simple requests**: 100-500ms
- **Document processing**: 2-5 seconds
- **Chat responses**: 1-3 seconds

### **Memory Usage**
- **Peak usage**: 800-1500MB (out of 2048MB)
- **Average usage**: 400-800MB
- **Idle usage**: 100-200MB

## 🚀 **Next Steps**

1. **Update Lambda configuration** with the commands above
2. **Monitor performance** for 24-48 hours
3. **Enable provisioned concurrency** if cold starts persist
4. **Optimize dependencies** if memory usage is high
5. **Set up alerts** for performance issues

## 📞 **Support**

If issues persist after optimization:
1. Check CloudWatch logs for specific errors
2. Monitor Lambda metrics in AWS Console
3. Test with the provided scripts
4. Review the deployment guide for configuration issues

---

**Note**: The authentication is working correctly. The timeout issue is primarily a performance optimization concern that can be resolved with the above recommendations. 