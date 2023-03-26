from enum import Enum
import uuid
import pytest
import requests

from tests.integration.create_user import CognitoUser


def generate_test_email():
    random_uuid = str(uuid.uuid4())
    return f"peoplefromgoodhomes+{random_uuid}@gmail.com"


class API(Enum):
    USER = 1
    MERCHANT = 2

    def url(self, path: str):
        if self == API.USER:
            return f"https://rtabkvdg1f.execute-api.us-east-1.amazonaws.com/Prod{path}"
        elif self == API.MERCHANT:
            return f"https://opuzgns4yi.execute-api.us-east-1.amazonaws.com/Prod{path}"
        else:
            raise ValueError("Invalid APIType")


@pytest.mark.asyncio
async def test_integration():

    # create a merchant
    merchant_pool_id = "us-east-1_2GdINgnSJ"  # merchant pool
    merchant_client_id = "4mn3rkpjkn0qgqqgpj11tjdtgd"
    merchant = CognitoUser(
        user_pool_id=merchant_pool_id, client_id=merchant_client_id, email=generate_test_email(), password="password123"
    )
    await merchant.create_user_and_login()
    assert(merchant.is_logged_in() is True)

    # create a user
    user_pool_id = "us-east-1_1KWE8lEIA"  # user pool
    user_client_id = "3d2h5fs9unkhnpdk8vkc5q9p90"
    user = CognitoUser(
        user_pool_id=user_pool_id, client_id=user_client_id, email=generate_test_email(), password="password123"
    )
    await user.create_user_and_login()
    assert user.is_logged_in() is True

    # get balance of merchant, assert it's 0
    merchant_balance = requests.get(API.MERCHANT.url("/merchant/balance"), headers=merchant.authentication_headers)
    assert merchant_balance["response"]["balance"] == 0

    # get balance of user, assert it's equal to the signup bonus
    user_balance = requests.get(API.USER.url("/user/balance"), headers=user.authentication_headers)
    assert user_balance["response"]["balance"] == 0

    # redeem from a merchant for an amount

    # assert new balance of user is equal to the signup bonus minus the amount redeemed




