import boto3


class CognitoUser:

    def __init__(self, user_pool_id: str, client_id: str, email: str, password: str):
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.email = email
        self.password = password
        self.authentication_headers: dict = None
        self.sub: str = None

    def is_logged_in(self) -> bool:
        return self.authentication_headers is not None

    async def create_user_and_login(self) -> dict:
        user = await self.__create_user()
        await self.__update_password()
        client = await self.__login()
        return {"user": user, "client": client}

    async def __create_user(self):
        client = boto3.client('cognito-idp', region_name='us-east-1')
        response = client.admin_create_user(
            UserPoolId=self.user_pool_id,
            Username=self.email,
            TemporaryPassword="temporary_password",
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': self.email
                },
            ],
        )
        self.sub = response['User']['Username']
        return response

    async def __login(self) -> dict:
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

    async def __update_password(self) -> dict:
        client = boto3.client('cognito-idp', region_name='us-east-1')
        client.admin_set_user_password(
            UserPoolId=self.user_pool_id,
            Username=self.email,
            Password=self.password,
            Permanent=True  # set to False if the user is required to change their password on next login
        )
