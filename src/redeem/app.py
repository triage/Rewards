import os
import json

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools import Logger
from aws_lambda_powertools import Tracer
from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit
from pyqldb.driver.qldb_driver import QldbDriver
from pyqldb.config.retry_config import RetryConfig

app = APIGatewayRestResolver()
tracer = Tracer()
logger = Logger()
metrics = Metrics(namespace="Powertools")


@app.post("/merchant/redeem")
@tracer.capture_method
def redeem():
    event = app.current_event
    metrics.add_metric(name="RedeemInvocations", unit=MetricUnit.Count, value=1)

    # structured log
    # See: https://awslabs.github.io/aws-lambda-powertools-python/latest/core/logger/
    logger.info("Merchant API - Redeem- HTTP 200")
    merchant_sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    body = json.loads(event["body"])
    user_sub, amount, key, merchant_description, user_description =\
        body["user_sub"], body["amount"], body["key"], body["merchant_description"], body["user_description"]

    logger.info(f"key:{key}")
    retry_config = RetryConfig(retry_limit=3)
    qldb_driver = QldbDriver(ledger_name=os.environ.get("LEDGER_NAME"), retry_config=retry_config)

    def execute_transaction(transaction_executor):

        def get_balance_for_sub(sub):
            try:
                cursor = transaction_executor.execute_statement("SELECT balance from balances WHERE sub = ?", sub)
                first_record = next(cursor, None)
                if first_record:
                    return first_record["balance"]
                else:
                    raise Exception("User does not exist")
            except Exception as e:
                raise e

        merchant_balance = get_balance_for_sub(merchant_sub)
        user_balance = get_balance_for_sub(user_sub)

        if user_balance < amount:
            raise Exception("Insufficient balance")

        # update balances for each
        try:
            statement = f"UPDATE balances set balance = {merchant_balance + amount}, \"key\"=\'{key}\' where sub=\'{merchant_sub}\'"
            transaction_executor.execute_statement(statement)
        except Exception as _:
            raise Exception("Unable to update merchant balance")

        try:
            statement = f"UPDATE balances set balance = {user_balance - amount}, \"key\" = \'{key}\' where sub=\'{user_sub}\'"
            transaction_executor.execute_statement(statement)
        except Exception as _:
            raise Exception("Unable to update user balance")

        # insert into a transaction for the user
        transaction_user = json.dumps({
            "id": "{key}-user".format(key=key),
            "key": key,
            "sub": user_sub,
            "amount": amount,
            "description": user_description
        }).replace("\"", "'")
        try:
            statement = f"INSERT into transactions VALUE {transaction_user}"
            transaction_executor.execute_statement(statement)
        except Exception as _:
            raise Exception("Unable to insert transactions into user")

        # insert a transaction for the merchant
        transaction_merchant = json.dumps({
            "id": "{key}-merchant".format(key=key),
            "key": key,
            "sub": merchant_sub,
            "amount": amount,
            "description": merchant_description
        }).replace("\"", "'")

        try:
            statement = f"INSERT into transactions VALUE {transaction_merchant}"
            transaction_executor.execute_statement(statement)
        except Exception as _:
            raise Exception("Unable to insert transaction into merchant")

    qldb_driver.execute_lambda(lambda executor: execute_transaction(executor))

    return {"key": key}


# Enrich logging with contextual information from Lambda
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
# Adding tracer
# See: https://awslabs.github.io/aws-lambda-powertools-python/latest/core/tracer/
@tracer.capture_lambda_handler
# ensures metrics are flushed upon request completion/failure and capturing ColdStart metric
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
