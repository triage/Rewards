class QLDBError(Exception):
    pass


class InsertTransactionError(QLDBError):
    def __init__(self, exception: Exception):
        super().__init__(f'Error inserting into transactions exception:{exception}')


class UpdateBalanceError(QLDBError):
    def __init__(self, exception: Exception):
        super().__init__(f'Error updating into balances - exception:{exception}')


class QLDBHelper:
    @classmethod
    def insert_transaction(cls, values: object, executor: object):
        """
        :type values: dict
        :param values: a dictionary of the values to insert

        :type executor: lambda executor
        :param executor: object that contains the function execute_statement

        :raises InsertError: If insert fails

        """
        try:
            statement = f"INSERT INTO transactions VALUE ?"
            executor.execute_statement(statement, values)
        except Exception as exception:
            raise InsertTransactionError(exception=exception)

    @classmethod
    def update_balance(cls, sub: str, key: str, balance: int, executor: object):
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
