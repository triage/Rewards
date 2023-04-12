import os
from typing import Protocol, Optional, Any

from pyqldb.config.retry_config import RetryConfig
from pyqldb.cursor.stream_cursor import StreamCursor
from pyqldb.driver.qldb_driver import QldbDriver


class QLDBTransactionExecutor(Protocol):
    def execute_statement(self, statement: str, *parameters) -> StreamCursor:
        pass


class Driver(Protocol):
    def execute_lambda(self, lambda_func: ()) -> any:
        pass


class RewardsDAOError(Exception):
    pass


class InsertTransactionError(RewardsDAOError):
    pass


class UpdateBalanceError(RewardsDAOError):
    pass


class GetBalanceError(RewardsDAOError):
    pass


class RewardsDAO:

    executor: any

    def __init__(self, driver: Driver):
        self.driver = driver
        if driver is None:
            self.driver = QldbDriver(
                ledger_name=os.environ.get("LEDGER_NAME"),
                retry_config=RetryConfig(retry_limit=3)
            )

    def execute_transaction(self, lambda_func) -> any:
        def block(executor):
            self.executor = executor
            return lambda_func(self)
        return self.driver.execute_lambda(lambda executor: block(executor=executor))

    def get_transaction(self, key: str) -> Optional[dict]:
        try:
            cursor = self.executor.execute_statement("SELECT * FROM transactions WHERE \"key\" = ?", key)

            first_record = next(cursor, None)
            if first_record:
                return first_record
            else:
                return None
        except Exception as e:
            raise e

    def get_balance(self, sub: str) -> int:
        try:
            cursor = self.executor.execute_statement("SELECT balance FROM balances WHERE sub = ?", sub)
            first_record = next(cursor, None)
            if first_record:
                return first_record["balance"]
            else:
                raise GetBalanceError(exception=Exception(f"Unable to get balance for user:{sub}"))
        except Exception as e:
            raise e

    def insert_transaction(self, values: dict):
        """
        :type values: dict
        :param values: a dictionary of the values to insert

        :raises InsertError: If insert fails

        :return: id of the inserted record

        """
        transaction_id = values.get("id")
        if not transaction_id:
            raise InsertTransactionError(exception=Exception("id is required"))
        cursor = self.executor.execute_statement("SELECT * FROM transactions WHERE id = ?", transaction_id)
        # Check if there is any record in the cursor
        first_record = next(cursor, None)

        if first_record:
            # Record already exists, no need to insert
            raise InsertTransactionError(exception=Exception(f"Transaction already exists for id:{transaction_id}"))
        else:
            try:
                statement = f"INSERT INTO transactions VALUE ?"
                self.executor.execute_statement(statement, values)
            except Exception as exception:
                raise InsertTransactionError(exception=exception)
        return id

    def insert_balance(self, sub: str, key: str):
        """
        :type sub: str
        :param sub of the user attempting to change balance for

        :type key: str
        :param key: transaction key

        :raises InsertError: If insert fails

        """
        values = {
            "key": key,
            "balance": 0,
            "sub": sub
        }
        try:
            statement = f"INSERT INTO balances VALUE ?"
            self.executor.execute_statement(statement, values)
        except Exception as exception:
            raise InsertTransactionError(exception=exception)
        return key

    def update_balance(self, sub: str, key: str, balance: int):
        """
        :type sub: str
        :param sub of the user attempting to change balance for

        :type key: str
        :param key: transaction key

        :type balance: int
        :param balance: updated balance

        :raises UpdateBalanceError: If update fails

        """
        try:
            self.executor.execute_statement("UPDATE balances SET balance = ?, \"key\" = ? WHERE sub = ?", balance, key, sub)
        except Exception as exception:
            raise UpdateBalanceError(exception=exception)
