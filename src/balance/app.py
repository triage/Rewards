import os

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools import Logger
from aws_lambda_powertools import Tracer
from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit
from pyqldb.driver.qldb_driver import QldbDriver
from pyqldb.config.retry_config import RetryConfig
from qldb_helper.qldb_helper import QLDBHelper, Driver

app = APIGatewayRestResolver()
tracer = Tracer()
logger = Logger()
metrics = Metrics(namespace="Powertools")


@tracer.capture_method
def get_balance(qldb_driver: Driver = None, event: APIGatewayRestResolver = None, context: LambdaContext = None):
    if not event:
        event = app.current_event
    # adding custom metrics
    # See: https://awslabs.github.io/aws-lambda-powertools-python/latest/core/metrics/
    metrics.add_metric(name="BalanceInvocations", unit=MetricUnit.Count, value=1)

    # structured log
    # See: https://awslabs.github.io/aws-lambda-powertools-python/latest/core/logger/
    logger.info("LedgerStore API - /balance HTTP 200")
    logger.info("event: {event}", event=event)
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    retry_config = RetryConfig(retry_limit=3)
    if not qldb_driver:
        qldb_driver = QldbDriver(ledger_name=os.environ.get("LEDGER_NAME"), retry_config=retry_config)

    def read_documents(transaction_executor):
        return QLDBHelper.get_balance(sub=sub, executor=transaction_executor)

    # Query the table
    balance = qldb_driver.execute_lambda(lambda executor: read_documents(executor))

    return {"balance": balance, "sub": sub}


# Enrich logging with contextual information from Lambda
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
# Adding tracer
# See: https://awslabs.github.io/aws-lambda-powertools-python/latest/core/tracer/
@tracer.capture_lambda_handler
# ensures metrics are flushed upon request completion/failure and capturing ColdStart metric
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
