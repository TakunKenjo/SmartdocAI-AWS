import requests
import json
from datetime import datetime
import boto3
from config import AWS_DEFAULT_REGION, DYNAMODB_USERS_TABLE

url = 'https://cjmuk77ux2xovezfuxn2syuw2u0gelhz.lambda-url.us-east-1.on.aws/api/auth/register'

email = f'test-register-{int(datetime.now().timestamp())}@example.com'
data = {
    'email': email,
    'password': 'TestPass123!',
    'fullname': 'Test Register',
    'phone': '0901234567',
    'dob': '1990-01-01'
}

print(f'Testing register with new Function URL')
print(f'Email: {email}')
print()

try:
    resp = requests.post(url, json=data, timeout=30)
    print(f'Status: {resp.status_code}')
    result = resp.json()
    print(f'Response:\n{json.dumps(result, indent=2)}')
    
    if 'user_id' in result:
        user_id = result['user_id']
        
        # Check DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name=AWS_DEFAULT_REGION)
        table = dynamodb.Table(DYNAMODB_USERS_TABLE)
        
        print(f'\nChecking DynamoDB for user_id: {user_id}')
        response = table.get_item(Key={'user_id': user_id})
        if 'Item' in response:
            item = response['Item']
            print(f'✅ Profile created in DynamoDB!')
            print(f'   Email: {item.get("email")}')
            print(f'   email_verified: {item.get("email_verified")}')
            print(f'   verification_pending_until: {item.get("verification_pending_until")}')
        else:
            print(f'❌ Profile NOT in DynamoDB')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
