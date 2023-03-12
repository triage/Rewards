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


@app.get("/merchant/redeem")
@tracer.capture_method
def get_balance():
    event = app.current_event
    context = app.context
    # adding custom metrics
    # See: https://awslabs.github.io/aws-lambda-powertools-python/latest/core/metrics/
    metrics.add_metric(name="RedeemInvocations", unit=MetricUnit.Count, value=1)

    # structured log
    # See: https://awslabs.github.io/aws-lambda-powertools-python/latest/core/logger/
    logger.info("Merchant API - Redeem- HTTP 200")
    merchant_sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    body = json.loads(event["body"])
    user_sub, amount, key, merchant_description, user_description =\
        body["user"], body["amount"], body["key"], body["merchant_description"], body["user_description"]

    retry_config = RetryConfig(retry_limit=3)
    qldb_driver = QldbDriver(ledger_name=os.environ.get("LEDGER_NAME"), retry_config=retry_config)

    def read_documents(transaction_executor):

        def get_balanceForSub(sub):
            try:
                cursor = transaction_executor.execute_statement("SELECT balance from balances WHERE sub = ?", sub)
                first_record = next(cursor, None)
                if first_record:
                    return first_record["balance"]
                else:
                    raise Exception("User does not exist")
            except Exception as e:
                raise e

        merchant_balance = get_balanceForSub(merchant_sub)
        user_balance = get_balance(user_sub)

        if user_balance < amount:
            raise Exception("Insufficient balance")

        # update balances for each
        transaction_executor.execute_statement(f"UPDATE balances set balance = ${merchant_balance} where sub=${merchant_sub}")
        transaction_executor.execute_statement(f"UPDATE balances set balance = ${user_balance - amount} where sub=${user_sub}")

        # insert into a transaction for the user
        transaction_user = {
            "key": key,
            "sub": user_sub,
            "amount": amount,
            "description": user_description
        }
        transaction_executor.execute_statementf(f"INSERT into transactions VALUE ${json.dumps(transaction_user)}")

        # insert a transaction for the merchant
        transaction_merchant = {
            "key": key,
            "sub": merchant_sub,
            "amount": amount,
            "description": merchant_description
        }
        transaction_executor.execute_statementf(f"INSERT into transactions VALUE ${json.dumps(transaction_merchant)}")

    qldb_driver.execute_lambda(lambda executor: read_documents(executor))

    return True


# Enrich logging with contextual information from Lambda
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
# Adding tracer
# See: https://awslabs.github.io/aws-lambda-powertools-python/latest/core/tracer/
@tracer.capture_lambda_handler
# ensures metrics are flushed upon request completion/failure and capturing ColdStart metric
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
