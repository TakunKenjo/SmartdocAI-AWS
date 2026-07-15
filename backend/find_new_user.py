import boto3
from datetime import datetime
from config import AWS_DEFAULT_REGION, COGNITO_USER_POOL_ID, DYNAMODB_USERS_TABLE

cognito = boto3.client('cognito-idp', region_name=AWS_DEFAULT_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_DEFAULT_REGION)
table = dynamodb.Table(DYNAMODB_USERS_TABLE)

print("🔍 Finding new unconfirmed users (missing in DynamoDB)...\n")

# Get all users from Cognito
paginator = cognito.get_paginator('list_users')
pages = paginator.paginate(UserPoolId=COGNITO_USER_POOL_ID)

users_in_cognito = {}
for page in pages:
    for user in page['Users']:
        user_id = user['Username']
        status = user['UserStatus']
        email = next((attr['Value'] for attr in user['Attributes'] if attr['Name'] == 'email'), 'N/A')
        created = user['UserCreateDate']
        users_in_cognito[user_id] = {'email': email, 'status': status, 'created': created}

# Get all profiles from DynamoDB
response = table.scan()
users_in_dynamodb = set(item['user_id'] for item in response['Items'])

# Find unconfirmed users not in DynamoDB
missing = []
for user_id, info in users_in_cognito.items():
    if info['status'] == 'UNCONFIRMED' and user_id not in users_in_dynamodb:
        missing.append((user_id, info['email'], info['created']))

# Sort by creation time (newest first)
missing.sort(key=lambda x: x[2], reverse=True)

if missing:
    print(f"❌ Found {len(missing)} UNCONFIRMED user(s) missing in DynamoDB:\n")
    for i, (user_id, email, created) in enumerate(missing[:5], 1):
        print(f"{i}. {email}")
        print(f"   User ID: {user_id}")
        print(f"   Created: {created}\n")
else:
    print("✅ All UNCONFIRMED users have DynamoDB profiles!")
