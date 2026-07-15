import requests
import json
from datetime import datetime

lambda_url = "https://tqmbkpswubye2ubwg2lc2s7ele0ffbzz.lambda-url.us-east-1.on.aws"

# Test data
test_data = {
    "email": f"test-register-{int(datetime.now().timestamp())}@example.com",
    "password": "TestPass123!",
    "fullname": "Test User",
    "phone": "0901234567",
    "dob": "1990-01-01"
}

print(f"📤 Registering: {test_data['email']}\n")

try:
    response = requests.post(
        f"{lambda_url}/api/auth/register",
        json=test_data,
        timeout=30
    )
    
    print(f"Status: {response.status_code}\n")
    result = response.json()
    
    if 'user_id' in result:
        print(f"✅ Success!")
        print(f"   User ID: {result['user_id']}")
        print(f"   Email: {result['email']}")
        print(f"   Message: {result['message']}\n")
        
        # Now check DynamoDB
        import boto3
        from config import AWS_DEFAULT_REGION, DYNAMODB_USERS_TABLE
        
        dynamodb = boto3.resource('dynamodb', region_name=AWS_DEFAULT_REGION)
        table = dynamodb.Table(DYNAMODB_USERS_TABLE)
        
        user_id = result['user_id']
        response = table.get_item(Key={'user_id': user_id})
        
        if 'Item' in response:
            print(f"✅ DynamoDB: Profile created!")
            item = response['Item']
            print(f"   Email: {item.get('email')}")
            print(f"   email_verified: {item.get('email_verified')}")
            print(f"   verification_pending_until: {item.get('verification_pending_until')}")
        else:
            print(f"❌ DynamoDB: Profile NOT created!")
    else:
        print(f"❌ Error: {result}")
        
except Exception as e:
    print(f"❌ Error: {e}")
