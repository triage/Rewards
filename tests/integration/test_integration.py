import uuid
import pytest

from tests.integration.create_user import CognitoUser


def generate_test_email():
    random_uuid = str(uuid.uuid4())
    return f"test_{random_uuid}@strategicinformationservices.com"


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

    user_pool_id = "us-east-1_1KWE8lEIA"  # user pool
    user_client_id = "3d2h5fs9unkhnpdk8vkc5q9p90"

    user = CognitoUser(
        user_pool_id=user_pool_id, client_id=user_client_id, email=generate_test_email(), password="password123"
    )
    await user.create_user_and_login()

    assert user.is_logged_in() is True


