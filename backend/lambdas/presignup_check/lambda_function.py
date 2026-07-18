import logging

import boto3


logger = logging.getLogger()
logger.setLevel(logging.INFO)

cognito = boto3.client("cognito-idp")


def _is_native_user(user, email):
    username = user.get("Username", "")
    return username.lower() == email.lower()


def _is_external_user(user):
    username = user.get("Username", "")
    return "_" in username and "@" not in username


def _provider_subject_from_username(username, provider_name):
    prefix = f"{provider_name}_"
    if username.startswith(prefix):
        return username[len(prefix):]
    return username.split("_", 1)[1] if "_" in username else username


def lambda_handler(event, context):
    user_pool_id = event["userPoolId"]
    trigger_source = event["triggerSource"]
    incoming_username = event["userName"]
    email = event["request"].get("userAttributes", {}).get("email")

    logger.info(
        "PreSignUp trigger_source=%s incoming_username=%s email=%s",
        trigger_source,
        incoming_username,
        email,
    )

    if not email:
        return event

    response = cognito.list_users(
        UserPoolId=user_pool_id,
        Filter=f'email = "{email}"'
    )
    users = response.get("Users", [])
    existing_users = [user for user in users if user.get("Username") != incoming_username]
    native_user = next((user for user in existing_users if _is_native_user(user, email)), None)
    external_user = next((user for user in existing_users if _is_external_user(user)), None)

    if trigger_source == "PreSignUp_ExternalProvider":
        if native_user:
            provider_name = incoming_username.split("_", 1)[0]
            provider_subject = _provider_subject_from_username(incoming_username, provider_name)
            destination_username = native_user["Username"]

            logger.info(
                "Linking external provider %s subject=%s to native username=%s",
                provider_name,
                provider_subject,
                destination_username,
            )

            cognito.admin_link_provider_for_user(
                UserPoolId=user_pool_id,
                DestinationUser={
                    "ProviderName": "Cognito",
                    "ProviderAttributeValue": destination_username,
                },
                SourceUser={
                    "ProviderName": provider_name,
                    "ProviderAttributeName": "Cognito_Subject",
                    "ProviderAttributeValue": provider_subject,
                },
            )

        event["response"]["autoConfirmUser"] = True
        event["response"]["autoVerifyEmail"] = True
        return event

    if trigger_source == "PreSignUp_SignUp":
        if external_user and not native_user:
            raise Exception(
                "Email nay da duoc dang nhap bang Google. Vui long dang nhap bang Google."
            )
        return event

    return event