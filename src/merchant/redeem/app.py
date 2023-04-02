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
from qldb_helper import QLDBHelper, Driver
from redeem.transaction_approver import transaction_should_approve

app = APIGatewayRestResolver()
tracer = Tracer()
logger = Logger()
metrics = Metrics(namespace="Powertools")

table_name=os.environ.get("IDEMPOTENCY_TABLE_NAME")\
    if os.environ.get("IDEMPOTENCY_TABLE_NAME") is not None else "ledgerstore-dev-IdempotencyTable-8OIO7OUQBFCJ"
persistence_layer = DynamoDBPersistenceLayer(table_name)


class RedeemError(Exception):
    pass


@tracer.capture_method
def redeem(event: dict, context: LambdaContext, qldb_driver: Driver = None):
    metrics.add_metric(name="RedeemInvocations", unit=MetricUnit.Count, value=1)

    merchant_sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    body = json.loads(event["body"])
    user_sub, amount, key, merchant_description, user_description = \
        body["user_sub"], int(body["amount"]), body["key"], body["merchant_description"], body["user_description"]

    if not qldb_driver:
        qldb_driver = QldbDriver(
            ledger_name=os.environ.get("LEDGER_NAME"),
            retry_config=RetryConfig(retry_limit=3)
        )

    def execute_transaction(transaction_executor):

        merchant_balance = QLDBHelper.get_balance(sub=merchant_sub, executor=transaction_executor)
        user_balance = QLDBHelper.get_balance(sub=user_sub, executor=transaction_executor)

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
            "id": f"{key}-user",
            "key": key,
            "sub": user_sub,
            "merchant_sub": merchant_sub,
            "amount": -amount,
            "description": user_description
        }, executor=transaction_executor)

        # insert a transaction for the merchant
        QLDBHelper.insert_transaction(values={
            "id": f"{key}-merchant",
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
    logger.info(event)
    return redeem(event=event, context=context)
