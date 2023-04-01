from typing import Protocol

from pyqldb.cursor.stream_cursor import StreamCursor


def foo() -> int:
    return 1


class QLDBTransactionExecutor(Protocol):
    def execute_statement(self, statement: str, *parameters) -> StreamCursor:
        pass


class QLDBError(Exception):
    pass


class InsertTransactionError(QLDBError):
    def __init__(self, exception: Exception):
        super().__init__(f'Error inserting into transactions exception:{exception}')


class UpdateBalanceError(QLDBError):
    def __init__(self, exception: Exception):
        super().__init__(f'Error updating into balances - exception:{exception}')


class GetBalanceError(QLDBError):
    pass


class QLDBHelper:
    @classmethod
    def get_balance(cls, sub: str, executor: QLDBTransactionExecutor) -> int:
        try:
            cursor = executor.execute_statement("SELECT balance from balances WHERE sub = ?", sub)
            first_record = next(cursor, None)
            if first_record:
                return first_record["balance"]
            else:
                raise GetBalanceError(f"Unable to get balance for user:{sub}")
        except Exception as e:
            raise e

    @classmethod
    def insert_transaction(cls, values: dict, executor: QLDBTransactionExecutor):
        """
        :type values: dict
        :param values: a dictionary of the values to insert

        :type executor: lambda executor
        :param executor: object that contains the function execute_statement

        :raises InsertError: If insert fails

        :return: id of the inserted record

        """
        transaction_id = values.get("id")
        if not transaction_id:
            raise InsertTransactionError(Exception("id is required"))
        cursor = executor.execute_statement("SELECT * FROM transactions WHERE id = ?", transaction_id)
        # Check if there is any record in the cursor
        first_record = next(cursor, None)

        if first_record:
            # Record already exists, no need to insert
            pass
        else:
            try:
                statement = f"INSERT INTO transactions VALUE ?"
                executor.execute_statement(statement, values)
            except Exception as exception:
                raise InsertTransactionError(exception=exception)
        return id

    @classmethod
    def insert_balance(cls, sub: str, key: str, executor: QLDBTransactionExecutor):
        """
        :type sub: str
        :param sub of the user attempting to change balance for

        :type key: str
        :param key: transaction key

        :type executor: lambda executor
        :param executor: object that contains the function execute_statement

        :raises InsertError: If insert fails

        """
        # This is critical to make this transaction idempotent
        cursor = executor.execute_statement("SELECT * FROM balances WHERE id = ?", sub)
        # Check if there is any record in the cursor
        first_record = next(cursor, None)

        if first_record:
            # Record already exists, no need to insert
            pass
        else:
            values = {
                "key": key,
                "balance": 0,
                "sub": sub
            }
            try:
                statement = f"INSERT INTO balances VALUE ?"
                executor.execute_statement(statement, values)
            except Exception as exception:
                raise InsertTransactionError(exception=exception)
        return key

    @classmethod
    def update_balance(cls, sub: str, key: str, balance: int, executor: QLDBTransactionExecutor):
        """
        :type sub: str
        :param sub of the user attempting to change balance for

        :type key: str
        :param key: transaction key

        :type balance: int
        :param balance: updated balance

        :type executor: lambda executor
        :param executor: object that contains the function execute_statement

        :raises UpdateBalanceError: If update fails

        """
        try:
            executor.execute_statement("UPDATE balances SET balance = ?, \"key\" = ? WHERE sub = ?", balance, key, sub)
        except Exception as exception:
            raise UpdateBalanceError(exception=exception)
