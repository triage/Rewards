import base64

import boto3
import hmac
import hashlib


class CognitoUser:

    def __init__(self, client_id: str, client_secret: str, email: str, password: str):
        self.client_id = client_id
        self.email = email
        self.password = password
        self.authentication_headers: dict
        self.sub: str
        self.client_secret = client_secret

    def is_logged_in(self) -> bool:
        return self.authentication_headers is not None

    async def create_user_and_login(self) -> dict:
        user = await self.__create_user()
        client = await self.__login()
        return {"user": user, "client": client}

    async def __create_user(self):
        client = boto3.client('cognito-idp', region_name='us-east-1')
        response = client.sign_up(
            ClientId=self.client_id,
            SecretHash=self.__calculate_secret_hash(),
            Username=self.email,
            Password="temporary_password",
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': self.email
                },
            ],
        )
        self.sub = response['User']['Username']
        return response

    def __calculate_secret_hash(self):
        key = bytes(self.client_secret, 'utf-8')
        message = bytes(f'{self.email}{self.client_id}', 'utf-8')
        return base64.b64encode(hmac.new(key, message, digestmod=hashlib.sha256).digest()).decode()

    async def __login(self):
        client = boto3.client('cognito-idp', region_name='us-east-1')
        response = client.initiate_auth(
            ClientId=self.client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': self.email,
                'PASSWORD': self.password
            },
        )
        token = response['AuthenticationResult']['IdToken']
        headers = {'Authorization': f'Bearer {token}'}
        self.authentication_headers = headers
