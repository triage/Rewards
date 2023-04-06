from unittest.mock import MagicMock, Mock
from src.rewards_dao.rewards_dao import Driver
from pyqldb.communication.session_client import SessionClient
from pyqldb.cursor.stream_cursor import StreamCursor


class MockExecutor:
    def __init__(self, responses: dict):
        self.responses = responses
        self.queries = []

    def execute_statement(self, statement: str, *parameters) -> StreamCursor:
        formatted_query = statement.replace('?', '%s') % parameters
        self.queries.append(formatted_query)
        statement_result = self.responses[formatted_query]

        # create a mock cursor object
        cursor_mock = MagicMock()

        # define the return values for the cursor's __next__ method
        cursor_mock.__next__.side_effect = [statement_result, StopIteration]

        return cursor_mock


class MockQLDBDriver(Driver):
    def __init__(self, responses: dict):
        self.responses = responses
        self.session = Mock(spec=SessionClient)
        self.executor = MockExecutor(responses)

    def execute_lambda(self, lambda_func: any) -> any:
        return lambda_func(self.executor)
