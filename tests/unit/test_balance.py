import json
import os
from unittest.mock import Mock, MagicMock
import pytest
from pyqldb.communication.session_client import SessionClient
from pyqldb.cursor.stream_cursor import StreamCursor
from src.balance import app
from src.qldb_helper.qldb_helper import Driver

class MockExecutor:
    def __init__(self, responses: dict):
        self.responses = responses

    def execute_statement(self, statement: str, *parameters) -> StreamCursor:
        formatted_query = statement.replace('?', '%s') % parameters
        statement_result = self.responses[formatted_query]

        # create a mock cursor object
        cursor_mock = MagicMock()

        # define the return values for the cursor's __next__ method
        cursor_mock.__next__.side_effect = [statement_result, StopIteration]

        return cursor_mock


class MockQLDBDriver(Driver):
    def __init__(self, responses: dict):
        self.responses = responses
        self.session = Mock(spec=SessionClient)
        self.executor = MockExecutor(responses)

    def execute_lambda(self, lambda_func: (MockExecutor)) -> any:
        return lambda_func(self.executor)


def lambda_context():
    class LambdaContext:
        def __init__(self):
            self.function_name = "test_balance"

    return LambdaContext()


@pytest.fixture()
def apigw_event():
    return {
        "body": "",
        "headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Host": "127.0.0.1:3000",
            "Sec-Ch-Ua": "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "\"Linux\"",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
            "X-Forwarded-Port": "3000",
            "X-Forwarded-Proto": "http"
        },
        "httpMethod": "GET",
        "isBase64Encoded": False,
        "multiValueHeaders": {
            "Accept": [
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
            ],
            "Accept-Encoding": [
                "gzip, deflate, br"
            ],
            "Accept-Language": [
                "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
            ],
            "Cache-Control": [
                "max-age=0"
            ],
            "Connection": [
                "keep-alive"
            ],
            "Host": [
                "127.0.0.1:3000"
            ],
            "Sec-Ch-Ua": [
                "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\""
            ],
            "Sec-Ch-Ua-Mobile": [
                "?0"
            ],
            "Sec-Ch-Ua-Platform": [
                "\"Linux\""
            ],
            "Sec-Fetch-Dest": [
                "document"
            ],
            "Sec-Fetch-Mode": [
                "navigate"
            ],
            "Sec-Fetch-Site": [
                "none"
            ],
            "Sec-Fetch-User": [
                "?1"
            ],
            "Upgrade-Insecure-Requests": [
                "1"
            ],
            "User-Agent": [
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"
            ],
            "X-Forwarded-Port": [
                "3000"
            ],
            "X-Forwarded-Proto": [
                "http"
            ]
        },
        "multiValueQueryStringParameters": "",
        "path": "/user/balance",
        "pathParameters": "",
        "queryStringParameters": "",
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "test-user-50000"
                }
            },
            "accountId": "123456789012",
            "apiId": "1234567890",
            "domainName": "127.0.0.1:3000",
            "extendedRequestId": "",
            "httpMethod": "GET",
            "identity": {
                "accountId": "",
                "apiKey": "",
                "caller": "",
                "cognitoAuthenticationProvider": "",
                "cognitoAuthenticationType": "",
                "cognitoIdentityPoolId": "",
                "sourceIp": "127.0.0.1",
                "user": "",
                "userAgent": "Custom User Agent String",
                "userArn": ""
            },
            "path": "/user/balance",
            "protocol": "HTTP/1.1",
            "requestId": "a3590457-cac2-4f10-8fc9-e47114bf7c62",
            "requestTime": "02/Feb/2023:11:45:26 +0000",
            "requestTimeEpoch": 1675338326,
            "resourceId": "123456",
            "resourcePath": "/user/balance",
            "stage": "Prod"
        },
        "resource": "/user/balance",
        "stageVariables": "",
        "version": "1.0"
    }


def test_balance(apigw_event):
    response = app.get_balance(qldb_driver=MockQLDBDriver(responses={
        "SELECT balance from balances WHERE sub = test-user-50000": {"balance": 50000},
    }), event=apigw_event, context=lambda_context())

    assert response["balance"] == 50000
    assert response["sub"] == "test-user-50000"
