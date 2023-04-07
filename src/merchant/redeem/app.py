import json
import os

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer, idempotent
)
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext
from rewards_dao import RewardsDAO, Driver
from transaction_approver import transaction_should_approve

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

    def execute_transaction(dao: RewardsDAO):
        user_balance = dao.get_balance(sub=user_sub)

        if not transaction_should_approve(balance=user_balance, transaction_amount=amount):
            raise RedeemError("Insufficient balance")

        dao.insert_transaction(values={
            "id": f"{key}-user",
            "key": key,
            "sub": user_sub,
            "merchant_sub": merchant_sub,
            "amount": -amount,
            "description": user_description
        })

        user_balance -= amount
        dao.update_balance(sub=user_sub, key=key, balance=user_balance)

        # merchant
        merchant_balance = dao.get_balance(sub=merchant_sub)
        merchant_balance += amount
        dao.update_balance(sub=merchant_sub, key=key, balance=merchant_balance)

        # insert into a transaction for the user
        dao.insert_transaction(values={
            "id": f"{key}-user",
            "key": key,
            "sub": user_sub,
            "merchant_sub": merchant_sub,
            "amount": -amount,
            "description": user_description
        })

        # insert a transaction for the merchant
        dao.insert_transaction(values={
            "id": f"{key}-merchant",
            "key": key,
            "sub": merchant_sub,
            "user_sub": user_sub,
            "amount": amount,
            "description": merchant_description
        })

    RewardsDAO(driver=qldb_driver).execute_transaction(lambda dao: execute_transaction(dao))

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
    return redeem(event=event, context=context)
