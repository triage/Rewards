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

        :return: id of the inserted record

        """
        id = values.get("id")
        if not id:
            raise InsertTransactionError(exception="id is required")
        cursor = executor.execute_statement("SELECT * FROM transactions WHERE id = ?", id)
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
    def insert_balance(cls, sub: str, key: str, executor: object):
        """
        :type sub: str
        :param sub of the user attempting to change balance for

        :type key: str
        :param key: transaction key

        :type executor: lambda executor
        :param executor: object that contains the function execute_statement

        :raises InsertError: If insert fails

        """
        # Check if doc with GovId:TOYENC486FH exists
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
