import pytest

from tests.qldb_mock import MockQLDBDriver
from src.qldb_helper.qldb_helper import QLDBHelper


def mock_qldb_driver(responses: dict):
    return MockQLDBDriver(responses=responses)


@pytest.fixture
def mock_qldb_driver_insert():
    return mock_qldb_driver(responses={
        'SELECT balance FROM balances WHERE sub = sub': None,
        "INSERT INTO balances VALUE {'key': 'key', 'balance': 0, 'sub': 'sub'}": None
    })


@pytest.fixture
def mock_qldb_driver_get_balance():
    return mock_qldb_driver(responses={
        'SELECT balance FROM balances WHERE sub = sub': {"balance": 10}
    })


@pytest.fixture
def mock_qldb_driver_update_balance():
    return mock_qldb_driver(responses={
        "UPDATE balances SET balance = 10, \"key\" = key WHERE sub = sub": None
    })


class TestQLDBDriver:
    def test_insert_balance(self, mock_qldb_driver_insert):
        QLDBHelper.insert_balance(sub="sub", key="key", executor=mock_qldb_driver_insert.executor)
        assert(
                mock_qldb_driver_insert.executor.queries[0] == "SELECT balance FROM balances WHERE sub = sub"
        )

        assert(
                mock_qldb_driver_insert.executor.queries[1] ==
                "INSERT INTO balances VALUE {'key': 'key', 'balance': 0, 'sub': 'sub'}"
        )

    def test_get_balance(self, mock_qldb_driver_get_balance):
        balance = QLDBHelper.get_balance(sub="sub", executor=mock_qldb_driver_get_balance.executor)
        assert(
                mock_qldb_driver_get_balance.executor.queries[0] == "SELECT balance FROM balances WHERE sub = sub"
        )
        assert balance == 10

    def test_update_balance(self, mock_qldb_driver_update_balance):
        QLDBHelper.update_balance(sub="sub", key="key", balance=10, executor=mock_qldb_driver_update_balance.executor)
        assert(
                mock_qldb_driver_update_balance.executor.queries[0] ==
                "UPDATE balances SET balance = 10, \"key\" = key WHERE sub = sub"
        )
