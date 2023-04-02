import json
import os
import pytest
from datetime import datetime

from src.merchant.redeem import app
from tests.unit.test_balance import MockQLDBDriver


def lambda_context():
    class LambdaContext:
        def __init__(self):
            self.function_name = "test-func"

    return LambdaContext()

transaction_key = f"random-transaction-key{datetime.now().timestamp()}"

@pytest.fixture()
def apigw_event():

    return {
        "body": "{\"user_sub\": \"test-user-420\", "
                "\"amount\": 1200, "
                "\"merchant_description\": \"Order #123456\", "
                "\"user_description\": \"Company A\", "
                f"\"key\": \"{transaction_key}\"}}",
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
        "httpMethod": "POST",
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
        "path": "/merchant/redeem",
        "pathParameters": "",
        "queryStringParameters": "",
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "test-merchant-1",
                }
            },
            "accountId": "123456789012",
            "apiId": "1234567890",
            "domainName": "127.0.0.1:3000",
            "extendedRequestId": "",
            "httpMethod": "POST",
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
            "path": "/merchant/redeem",
            "protocol": "HTTP/1.1",
            "requestId": "a3590457-cac2-4f10-8fc9-e47114bf7c62",
            "requestTime": "02/Feb/2023:11:45:26 +0000",
            "requestTimeEpoch": 1675338326,
            "resourceId": "123456",
            "resourcePath": "/merchant/redeem",
            "stage": "Prod"
        },
        "resource": "/merchant/redeem",
        "stageVariables": "",
        "version": "1.0"
    }


def skip_test_redeem(apigw_event):
    response = app.redeem(qldb_driver=MockQLDBDriver(responses={
        "SELECT balance from balances WHERE sub = test-user-50000": {"balance": 50000},
    }), event=apigw_event, context=lambda_context())
    assert response["key"] == transaction_key
