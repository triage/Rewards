import json
import os

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer, idempotent
)
from aws_lambda_powertools import Logger
from aws_lambda_powertools import Metrics
from aws_lambda_powertools import Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext
from pyqldb.config.retry_config import RetryConfig
from pyqldb.driver.qldb_driver import QldbDriver

from src.qldb.qldp_helper import QLDBHelper

app = APIGatewayRestResolver()
tracer = Tracer()
logger = Logger()
metrics = Metrics(namespace="Powertools")

table_name=os.environ.get("IDEMPOTENCY_TABLE_NAME")\
    if os.environ.get("IDEMPOTENCY_TABLE_NAME") is not None else "ledgerstore-dev-IdempotencyTable-8OIO7OUQBFCJ"
persistence_layer = DynamoDBPersistenceLayer(table_name)
class RedeemError(Exception):
    pass


@app.post("/merchant/redeem")
@tracer.capture_method
def redeem():
    event = app.current_event
    metrics.add_metric(name="RedeemInvocations", unit=MetricUnit.Count, value=1)

    merchant_sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    body = json.loads(event["body"])
    user_sub, amount, key, merchant_description, user_description = \
        body["user_sub"], int(body["amount"]), body["key"], body["merchant_description"], body["user_description"]

    retry_config = RetryConfig(retry_limit=3)
    qldb_driver = QldbDriver(ledger_name=os.environ.get("LEDGER_NAME"), retry_config=retry_config)

    def transaction_should_approve(balance: int, transaction_amount: int):
        """
        Return if all the requirements are met which allow this transaction to proceed.
        For now, this just tracks if the user has sufficient balance
        """
        return transaction_amount <= balance

    def execute_transaction(transaction_executor):
        def get_balance_for_sub(sub) -> int:
            try:
                cursor = transaction_executor.execute_statement("SELECT balance from balances WHERE sub = ?", sub)
                first_record = next(cursor, None)
                if first_record:
                    return first_record["balance"]
                else:
                    raise RedeemError(f"User does not exist:{sub}")
            except Exception as e:
                raise e

        merchant_balance = get_balance_for_sub(merchant_sub)
        user_balance = get_balance_for_sub(user_sub)

        if not transaction_should_approve(balance=user_balance, transaction_amount=amount):
            raise RedeemError("Insufficient balance")

        user_balance -= amount
        merchant_balance += amount

        # update balances for each:
        # user
        QLDBHelper.update_balance(sub=user_sub, key=key, balance=user_balance, executor=transaction_executor)

        # merchant
        QLDBHelper.update_balance(sub=merchant_sub, key=key, balance=merchant_balance, executor=transaction_executor)

        # insert into a transaction for the user
        QLDBHelper.insert_transaction(values={
            "id": "{key}-user".format(key=key),
            "key": key,
            "sub": user_sub,
            "merchant_sub": merchant_sub,
            "amount": -amount,
            "description": user_description
        }, executor=transaction_executor)

        # insert a transaction for the merchant
        QLDBHelper.insert_transaction(values={
            "id": "{key}-merchant".format(key=key),
            "key": key,
            "sub": merchant_sub,
            "user_sub": user_sub,
            "amount": amount,
            "description": merchant_description
        }, executor=transaction_executor)

    qldb_driver.execute_lambda(lambda executor: execute_transaction(executor))

    return {"key": key}


# Enrich logging with contextual information from Lambda
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
# Adding tracer
# See: https://awslabs.github.io/aws-lambda-powertools-python/latest/core/tracer/
@tracer.capture_lambda_handler
# ensures metrics are flushed upon request completion/failure and capturing ColdStart metric
@metrics.log_metrics(capture_cold_start_metric=True)
@idempotent(persistence_store=persistence_layer)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
