import pytest

from tests.qldb_mock import MockQLDBDriver
from rewards_dao import RewardsDAO


def mock_qldb_driver(responses: dict):
    return MockQLDBDriver(responses=responses)


@pytest.fixture
def mock_qldb_driver_insert():
    return mock_qldb_driver(responses={
        "INSERT INTO balances VALUE {'key': 'key', 'balance': 0, 'sub': 'sub_insert'}": {"key": "key"}
    })


@pytest.fixture
def mock_qldb_driver_get_balance():
    return mock_qldb_driver(responses={
        'SELECT balance FROM balances WHERE sub = sub_balance': {"balance": 10}
    })


@pytest.fixture
def mock_qldb_driver_update_balance():
    return mock_qldb_driver(responses={
        "UPDATE balances SET balance = 20, \"key\" = key WHERE sub = update_sub": None
    })


class TestRewardsDAO:
    def test_insert_balance(self, mock_qldb_driver_insert):

        def insert_balance(dao: RewardsDAO):
            dao.insert_balance(sub="sub_insert", key="key")

        RewardsDAO(driver=mock_qldb_driver_insert)\
            .execute_transaction(lambda dao: insert_balance(dao=dao))
        assert(
                mock_qldb_driver_insert.executor.queries[0] ==
                "INSERT INTO balances VALUE {'key': 'key', 'balance': 0, 'sub': 'sub_insert'}"
        )
    #

    def test_get_balance(self, mock_qldb_driver_get_balance):
        def get_balance(dao: RewardsDAO):
            return dao.get_balance(sub="sub_balance")

        balance = RewardsDAO(driver=mock_qldb_driver_get_balance).execute_transaction(lambda dao: get_balance(dao=dao))
        assert(
                mock_qldb_driver_get_balance.executor.queries[0] ==
                "SELECT balance FROM balances WHERE sub = sub_balance"
        )
        assert balance == 10

    def test_update_balance(self, mock_qldb_driver_update_balance):
        def update_balance(dao: RewardsDAO):
            return dao.update_balance(sub="update_sub", key="key", balance=20)

        RewardsDAO(driver=mock_qldb_driver_update_balance).execute_transaction(lambda dao: update_balance(dao=dao))
        assert(
                mock_qldb_driver_update_balance.executor.queries[0] ==
                "UPDATE balances SET balance = 20, \"key\" = key WHERE sub = update_sub"
        )