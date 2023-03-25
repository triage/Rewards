import boto3
import pytest


class CognitoUser:

    @classmethod
    async def create_user_and_login(cls, user_pool_id: str, client_id: str, email: str, password: str) -> dict:
        user = await cls.__create_user(user_pool_id, email, "test_password")
        await cls.__update_password(user_pool_id, email, password)
        client = await cls.__login(
            user_pool_id=user_pool_id, client_id=client_id, email=email, password=password
        )
        return {"user": user, "client": client}

    @classmethod
    async def __create_user(cls, user_pool_id: str, email: str, password: str):
        client = boto3.client('cognito-idp', region_name='us-east-1')
        response = client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            TemporaryPassword=password,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': email
                },
            ],
        )
        return response

    @classmethod
    async def __login(cls, user_pool_id: str, client_id: str, email: str, password: str) -> dict:
        client = boto3.client('cognito-idp', region_name='us-east-1')
        response = client.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password
            },
        )
        token = response['AuthenticationResult']['AccessToken']
        headers = {'Authorization': f'Bearer {token}'}
        return headers

    @classmethod
    async def __update_password(cls, user_pool_id: str, email: str, password: str) -> dict:
        client = boto3.client('cognito-idp', region_name='us-east-1')
        client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=email,
            Password=password,
            Permanent=True  # set to False if the user is required to change their password on next login
        )
