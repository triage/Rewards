import unittest

import pytest

from tests.unit.test_balance import MockQLDBDriver


@pytest.fixture
def mock_qldb_driver(responses: dict):
    return MockQLDBDriver(responses=responses)


@pytest.fixture
def mock_insert():
    return {
        'INSERT INTO balances (sub, balance) VALUES ("abc123", 10000)': {"inserted": True}
    }


class QLDBDriverTestCase(unittest.TestCase):
    def test_insert(self, mock_qldb_driver):



        self.assertEqual(True, False)  # add assertion here


if __name__ == '__main__':
    unittest.main()
