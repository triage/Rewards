import uuid
import pytest

from tests.integration.create_user import CognitoUser


def generate_test_email():
    random_uuid = str(uuid.uuid4())
    return f"test_{random_uuid}@strategicinformationservices.com"


@pytest.mark.asyncio
async def test_create_merchant():
    # create a merchant

    email = generate_test_email()
    password = "password"
    user_pool_id = "us-east-1_2GdINgnSJ"
    client_id = "4mn3rkpjkn0qgqqgpj11tjdtgd"

    merchant = await CognitoUser.create_user_and_login(user_pool_id=user_pool_id, client_id=client_id, email=email, password=password)
    assert merchant is not None


