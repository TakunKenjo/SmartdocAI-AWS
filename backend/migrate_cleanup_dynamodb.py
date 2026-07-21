"""
Migration: Xóa các attributes thừa khỏi tất cả items trong DynamoDB table smartdocai-user-profiles.

Attributes cần xóa (không còn dùng trong code):
  - subscription_plan
  - document_quota
  - documents_used
  - storage_quota_gb
  - user_preferences
  - email_verified
  - verification_attempts
  - verification_pending_until

Chạy: python migrate_cleanup_dynamodb.py
"""

import boto3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

TABLE_NAME = "smartdocai-user-profiles"
STALE_ATTRS = [
    "subscription_plan",
    "document_quota",
    "documents_used",
    "storage_quota_gb",
    "user_preferences",
    "email_verified",
    "verification_attempts",
    "verification_pending_until",
]

def main():
    dynamodb = boto3.resource("dynamodb", region_name=config.AWS_DEFAULT_REGION)
    table = dynamodb.Table(TABLE_NAME)

    print(f"Scanning table: {TABLE_NAME}")
    items = []
    response = table.scan(ProjectionExpression="user_id")
    items.extend(response.get("Items", []))
    while "LastEvaluatedKey" in response:
        response = table.scan(
            ProjectionExpression="user_id",
            ExclusiveStartKey=response["LastEvaluatedKey"]
        )
        items.extend(response.get("Items", []))

    print(f"Found {len(items)} items total")

    # Build REMOVE expression
    remove_expr = "REMOVE " + ", ".join(f"#{a}" for a in STALE_ATTRS)
    expr_names = {f"#{a}": a for a in STALE_ATTRS}

    updated = 0
    skipped = 0

    for item in items:
        user_id = item["user_id"]
        # Lấy item đầy đủ để check có attribute thừa không
        full = table.get_item(Key={"user_id": user_id}).get("Item", {})
        has_stale = any(a in full for a in STALE_ATTRS)

        if not has_stale:
            skipped += 1
            continue

        table.update_item(
            Key={"user_id": user_id},
            UpdateExpression=remove_expr,
            ExpressionAttributeNames=expr_names,
        )
        stale_found = [a for a in STALE_ATTRS if a in full]
        print(f"  ✅ {user_id[:8]}... removed: {stale_found}")
        updated += 1

    print(f"\nDone. Updated: {updated}, Already clean: {skipped}")

if __name__ == "__main__":
    main()
