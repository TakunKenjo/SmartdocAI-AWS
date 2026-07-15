import boto3
from config import AWS_DEFAULT_REGION, COGNITO_USER_POOL_ID, DYNAMODB_USERS_TABLE

cognito = boto3.client('cognito-idp', region_name=AWS_DEFAULT_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_DEFAULT_REGION)
table = dynamodb.Table(DYNAMODB_USERS_TABLE)

user_id = "64f8b448-1071-7087-dfb6-6b41014dbc06"

# Check Cognito
try:
    response = cognito.admin_get_user(
        UserPoolId=COGNITO_USER_POOL_ID,
        Username=user_id
    )
    email = next(attr['Value'] for attr in response['UserAttributes'] if attr['Name'] == 'email')
    status = response['UserStatus']
    print(f"✅ Cognito: {email} ({status})")
except Exception as e:
    print(f"❌ Cognito: {str(e)}")

# Check DynamoDB
try:
    response = table.get_item(Key={'user_id': user_id})
    if 'Item' in response:
        item = response['Item']
        print(f"✅ DynamoDB: {item.get('email', 'N/A')}")
        print(f"   email_verified: {item.get('email_verified', 'N/A')}")
        print(f"   verification_pending_until: {item.get('verification_pending_until', 'N/A')}")
    else:
        print(f"❌ DynamoDB: User NOT found")
except Exception as e:
    print(f"❌ DynamoDB error: {str(e)}")
