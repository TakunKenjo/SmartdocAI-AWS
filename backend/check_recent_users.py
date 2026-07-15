import boto3
from config import AWS_DEFAULT_REGION, DYNAMODB_USERS_TABLE

dynamodb = boto3.resource('dynamodb', region_name=AWS_DEFAULT_REGION)
table = dynamodb.Table(DYNAMODB_USERS_TABLE)

# Scan for recent users
response = table.scan(Limit=10)

print("✅ Latest users in DynamoDB:")
for item in sorted(response['Items'], key=lambda x: x.get('created_at', ''), reverse=True)[:5]:
    print(f"\n  • Email: {item.get('email', 'N/A')}")
    print(f"    User ID: {item.get('user_id')}")
    print(f"    email_verified: {item.get('email_verified')}")
    print(f"    verification_pending_until: {item.get('verification_pending_until', 'N/A')}")

print(f"\n\nTotal profiles in DynamoDB: {response['Count']}")
