import os

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools import Logger
from aws_lambda_powertools import Tracer
from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit
from rewards_dao import RewardsDAO, Driver

app = APIGatewayRestResolver()
tracer = Tracer()
logger = Logger()
metrics = Metrics(namespace="Powertools")


@app.get("/user/balance")
@app.get("/merchant/balance")
@tracer.capture_method
def get_balance(event: APIGatewayRestResolver = None,
                context: LambdaContext = None,
                qldb_driver: Driver = None):
    if not event:
        event = app.current_event

    metrics.add_metric(name="BalanceInvocations", unit=MetricUnit.Count, value=1)

    sub = event["requestContext"]["authorizer"]["claims"]["sub"]

    def execute_transaction(dao: RewardsDAO):
        return dao.get_balance(sub=sub)

    balance = RewardsDAO(driver=qldb_driver).execute_transaction(lambda dao: execute_transaction(dao))
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
