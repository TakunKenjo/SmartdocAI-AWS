# 📅 Scheduler Setup Documentation

**Current Implementation:** FastAPI + APScheduler  
**Date Updated:** 2026-07-15  
**Feature:** 5-minute email verification timeout + automatic cleanup

---

## 📋 Table of Contents

1. [Current Setup](#current-setup)
2. [How It Works](#how-it-works)
3. [Files Modified](#files-modified)
4. [Testing](#testing)
5. [Migration to CloudWatch](#migration-to-cloudwatch)
6. [Troubleshooting](#troubleshooting)

---

## ✅ Current Setup

**Implementation:** FastAPI + APScheduler  
**Cleanup Frequency:** Every 1 minute  
**Cost:** FREE (no additional cost)  
**Reliability:** Dependent on FastAPI process running 24/7

### Flow Diagram

```
FastAPI Startup
      ↓
APScheduler initialized
      ↓
Background job added: cleanup_unverified_users
      ↓
Every 1 minute → cleanup_unverified_users() executes
      ↓
Scan DynamoDB for expired unverified users
      ↓
Delete from Cognito → DynamoDB → S3
      ↓
Log results
```

---

## 🔧 How It Works

### **1. Initialization (app_api.py - startup)**

```python
@app.on_event("startup")
def startup_event():
    logger.info("Khởi động API server SmartDocAI...")
    init_scheduler()  # ← Initialize background jobs
```

### **2. Job Definition**

```python
def init_scheduler():
    scheduler = BackgroundScheduler()
    
    # Add cleanup job: every 1 minute
    scheduler.add_job(
        cleanup_unverified_users,      # Function to run
        'interval',                     # Trigger type
        minutes=1,                      # Run every 1 minute
        id='cleanup_unverified_users',  # Job ID
        max_instances=1                 # Prevent concurrent runs
    )
    
    scheduler.start()
```

### **3. Cleanup Execution**

When triggered, `cleanup_unverified_users()` from `modules/profile_service.py`:

```
1. Scan DynamoDB
   └─ Find: email_verified=false AND verification_pending_until < now

2. For each expired user:
   ├─ Delete from Cognito
   ├─ Delete from DynamoDB
   └─ Delete from S3 (avatars + documents)

3. Return results
   ├─ cleaned: count of deleted users
   ├─ failed: count of errors
   └─ details: individual status per user
```

### **4. Shutdown (app_api.py - on shutdown)**

```python
@app.on_event("shutdown")
def shutdown_event():
    if scheduler and scheduler.running:
        scheduler.shutdown()  # ← Gracefully stop scheduler
```

---

## 📝 Files Modified

### **backend/app_api.py**

**Changes:**
- Line ~19: Added `from apscheduler.schedulers.background import BackgroundScheduler`
- Line ~320-360: Added `init_scheduler()` function
- Line ~363-368: Updated `@app.on_event("startup")` to call `init_scheduler()`
- Line ~370-376: Added `@app.on_event("shutdown")` event handler

**Key sections:**

```python
# ═══════════════════════════════════════════════════════════════════
# BACKGROUND SCHEDULER: Cleanup unverified users
# ═══════════════════════════════════════════════════════════════════

scheduler = None

def init_scheduler():
    """Initialize APScheduler for background jobs."""
    global scheduler
    from modules.profile_service import cleanup_unverified_users
    
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        cleanup_unverified_users,
        'interval',
        minutes=1,
        id='cleanup_unverified_users',
        name='Cleanup unverified users (5-min timeout)',
        misfire_grace_time=60,
        max_instances=1
    )
    scheduler.start()
    logger.info("✅ Background Scheduler initialized")

@app.on_event("startup")
def startup_event():
    logger.info("Khởi động API server SmartDocAI...")
    init_scheduler()

@app.on_event("shutdown")
def shutdown_event():
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("🛑 Background Scheduler stopped")
```

### **Other Files (NOT Modified)**

- `backend/modules/profile_service.py` - No changes (already has cleanup_unverified_users())
- `backend/modules/auth_service.py` - No changes
- `backend/requirements.txt` - Need to add `apscheduler` if not present

---

## ✅ Installation

### **1. Install APScheduler**

```bash
pip install apscheduler
```

### **2. Update requirements.txt (if needed)**

```bash
# Check if already installed
pip freeze | grep apscheduler

# If not, add to requirements.txt
echo "apscheduler==3.10.4" >> backend/requirements.txt
pip install -r backend/requirements.txt
```

### **3. Deploy to Lambda**

```bash
cd backend
python deploy_to_lambda.py
```

---

## 🧪 Testing

### **1. Local Testing (dev)**

```bash
cd backend
python -m uvicorn app_api:app --reload --host 0.0.0.0 --port 8000
```

**Output should show:**
```
✅ Background Scheduler initialized
   └─ Job: cleanup_unverified_users (every 1 minute)
```

### **2. Check Scheduler Status**

```bash
# Create test endpoint to check scheduler status
curl http://localhost:8000/health

# Response:
{
  "status": "ok",
  "scheduler_running": true
}
```

### **3. Monitor Cleanup Runs**

Check logs for cleanup activity:

```bash
# Show logs from FastAPI
tail -f /var/log/smartdocai/app.log | grep cleanup

# Should see entries like:
[Cleanup] Bắt đầu cleanup unverified users
[Cleanup] Tìm thấy 0 users chưa xác thực hết timeout
[Cleanup] ✅ Hoàn thành: cleaned=0, failed=0
```

### **4. Test with Actual Unverified User**

```bash
# 1. Create test user
python test_lambda_invoke.py

# 2. Wait for cleanup to run (1 minute)
sleep 60

# 3. Check if user was deleted
aws cognito-idp admin-get-user \
  --user-pool-id us-east-1_3oq5wIiuu \
  --username test@example.com \
  --region us-east-1
# Should return: UserNotFoundException
```

---

## 🔄 Migration to CloudWatch

If you want to move from FastAPI APScheduler to AWS CloudWatch Events + Lambda:

### **Why Migrate?**

| Aspect | FastAPI | CloudWatch |
|--------|---------|-----------|
| Reliability | Depends on FastAPI running | AWS managed (99.99% SLA) |
| Fail recovery | Manual restart | Auto re-trigger |
| Cost | Free | ~$0.02-0.03/month |
| Maintenance | Update code + redeploy | Config only |
| Observability | App logs | CloudWatch Events + Logs |

### **Migration Steps**

#### **Step 1: Remove APScheduler from app_api.py**

Delete these lines:

```python
# DELETE these lines
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = None

def init_scheduler():
    ...

@app.on_event("startup")
def startup_event():
    logger.info("Khởi động API server SmartDocAI...")
    init_scheduler()

@app.on_event("shutdown")
def shutdown_event():
    ...
```

Replace with simple startup:

```python
@app.on_event("startup")
def startup_event():
    logger.info("Khởi động API server SmartDocAI...")
    # No scheduler here
```

#### **Step 2: Update Lambda Handler**

Add CloudWatch Events support to `app_api.py`:

```python
def lambda_handler(event, context):
    """
    Handle both HTTP (from Function URL) and CloudWatch Events
    """
    # Check if CloudWatch Events trigger
    if 'source' in event and event['source'] == 'aws.events':
        logger.info("🔔 CloudWatch Events trigger detected")
        
        from modules.profile_service import cleanup_unverified_users
        result = cleanup_unverified_users()
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
    
    # Otherwise, handle HTTP request normally
    from mangum import Mangum
    asgi_handler = Mangum(app, lifespan="off")
    return asgi_handler(event, context)
```

#### **Step 3: Create CloudWatch Events Rule**

```bash
# 1. Create rule (trigger every 1 minute)
aws events put-rule \
  --name smartdocai-cleanup-rule \
  --schedule-expression "rate(1 minute)" \
  --state ENABLED \
  --region us-east-1

# 2. Grant Lambda permission
aws lambda add-permission \
  --function-name smartdocai \
  --statement-id AllowCloudWatchInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:us-east-1:623035187993:rule/smartdocai-cleanup-rule \
  --region us-east-1

# 3. Add Lambda as target
aws events put-targets \
  --rule smartdocai-cleanup-rule \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:623035187993:function:smartdocai","RoleArn"="arn:aws:iam::623035187993:role/smartdocai-lambda-role" \
  --region us-east-1
```

#### **Step 4: Redeploy Lambda**

```bash
python deploy_to_lambda.py
```

#### **Step 5: Verify**

```bash
# Check rule created
aws events list-rules --region us-east-1 | grep smartdocai-cleanup-rule

# Check targets
aws events list-targets-by-rule --rule smartdocai-cleanup-rule --region us-east-1

# Check Lambda logs
aws logs tail /aws/lambda/smartdocai --follow --region us-east-1
```

---

## 🔍 Troubleshooting

### **Problem: Scheduler not running**

**Symptoms:**
- Users not deleted after 5 minutes
- Logs show: "scheduler_running": false

**Solutions:**

```bash
# 1. Check if FastAPI is running
curl http://localhost:8000/health

# 2. Check logs for startup errors
tail -100 /var/log/smartdocai/app.log | grep -i "scheduler\|error"

# 3. Check if cleanup_unverified_users() is importable
python -c "from modules.profile_service import cleanup_unverified_users; print('OK')"

# 4. Restart FastAPI
docker restart smartdocai-api  # or similar

# 5. Check requirements installed
pip freeze | grep apscheduler
```

### **Problem: APScheduler already running on different instance**

**Symptoms:**
- Logs show: "Scheduler already running"
- Multiple cleanup runs per minute

**Solution:**
- Set `max_instances=1` (already done in code)
- This prevents multiple concurrent runs

### **Problem: Cleanup job not executing**

**Symptoms:**
- Logs show scheduler started but no cleanup logs

**Solutions:**

```bash
# 1. Check if cleanup_unverified_users has any users to clean
python check_current_status.py

# 2. Check DynamoDB for verification_pending_until field
python -c "
import boto3
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('smartdocai-user-profiles')
response = table.scan(
    FilterExpression='email_verified = :false',
    ExpressionAttributeValues={':false': False}
)
for item in response['Items']:
    print(f\"{item['email']}: {item.get('verification_pending_until', 'N/A')}\")
"

# 3. Add debug logging to init_scheduler()
# Uncomment debug lines in app_api.py init_scheduler()
```

### **Problem: Lambda invocation from CloudWatch fails**

**Symptoms:**
- CloudWatch Events fires but Lambda not triggered
- Lambda logs show nothing

**Solutions:**

```bash
# 1. Check EventBridge rule is enabled
aws events describe-rule --name smartdocai-cleanup-rule --region us-east-1 | grep State

# 2. Check Lambda policy includes EventBridge
aws lambda get-policy --function-name smartdocai --region us-east-1

# 3. Check Lambda has required IAM permissions
aws iam get-role-policy \
  --role-name smartdocai-lambda-role \
  --policy-name CognitoAccess \
  --region us-east-1

# 4. Enable CloudWatch Logs for EventBridge
aws events put-rule \
  --name smartdocai-cleanup-rule \
  --schedule-expression "rate(1 minute)" \
  --state ENABLED \
  --event-bus-name default \
  --region us-east-1
```

---

## 📞 Support

For issues or questions:

1. **Check logs first:**
   ```bash
   tail -f /var/log/smartdocai/app.log
   ```

2. **Check scheduler status:**
   ```bash
   curl http://lambda-url/health
   ```

3. **Review this documentation:**
   - [How It Works](#how-it-works)
   - [Troubleshooting](#troubleshooting)
   - [Migration Guide](#migration-to-cloudwatch)

4. **Monitor CloudWatch:**
   - Lambda metrics: Invocations, Errors, Duration
   - DynamoDB metrics: ConsumedCapacity
   - Cognito metrics: Throttled requests

---

## 📚 References

- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [AWS CloudWatch Events](https://docs.aws.amazon.com/events/)
- [AWS Lambda + CloudWatch Events](https://docs.aws.amazon.com/events/latest/userguide/run-lambda-schedule.html)
- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)

---

**Last Updated:** 2026-07-15  
**Status:** ✅ Production Ready (FastAPI + APScheduler)
