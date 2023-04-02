import unittest

import pytest

from tests.unit.test_balance import MockQLDBDriver
from src.qldb_helper.qldb_helper import QLDBHelper


def mock_qldb_driver(responses: dict):
    return MockQLDBDriver(responses=responses)


@pytest.fixture
def mock_qldb_driver_insert():
    return mock_qldb_driver(responses={
        'SELECT * FROM balances WHERE id = sub': None,
        "INSERT INTO balances VALUE {'key': 'key', 'balance': 0, 'sub': 'sub'}": None
    })


class TestQLDBDriver:
    def test_insert_balance(self, mock_qldb_driver_insert):
        QLDBHelper.insert_balance(sub="sub", key="key", executor=mock_qldb_driver_insert.executor)
        assert(
                mock_qldb_driver_insert.executor.queries[0] == "SELECT * FROM balances WHERE id = sub"
        )

        assert(
                mock_qldb_driver_insert.executor.queries[1] ==
                "INSERT INTO balances VALUE {'key': 'key', 'balance': 0, 'sub': 'sub'}"
        )

