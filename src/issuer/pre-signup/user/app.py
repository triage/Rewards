import os

from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools import Logger
from aws_lambda_powertools import Tracer
from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit
from rewards_dao import RewardsDAO, Driver

tracer = Tracer()
logger = Logger()
metrics = Metrics(namespace="Powertools")


@tracer.capture_method
def signup_confirmation(event: dict, context: LambdaContext, qldb_driver: Driver = None):
    # adding custom metrics
    # See: https://awslabs.github.io/aws-lambda-powertools-python/latest/core/metrics/
    metrics.add_metric(name="SignupConfirmationInvocations", unit=MetricUnit.Count, value=1)

    # structured log
    # See: https://awslabs.github.io/aws-lambda-powertools-python/latest/core/logger/
    user_sub = event.get("userName")
    amount = int(os.environ.get("USER_SIGNUP_REWARD"))
    issuer_sub = "ISSUER"
    key = f"POST-SIGNUP-{user_sub}"
    description = "Created"

    def execute_signup_confirmation(dao):
        dao.insert_balance(sub=user_sub, key=f"user-initialize-{user_sub}")

        # insert into a transaction for the user
        dao.insert_transaction(values={
            "id": "{key}-user".format(key=key),
            "key": key,
            "sub": user_sub,
            "amount": amount,
            "description": description
        })

        # insert a transaction for the issuer
        dao.insert_transaction(values={
            "id": "{key}-issuer".format(key=key),
            "key": key,
            "sub": issuer_sub,
            "amount": -amount,
            "description": description,
            "user_sub": user_sub,
        })

        # update the balance to the new amount
        dao.update_balance(sub=user_sub, key=key, balance=amount)

    # Query the table
    # qldb_driver.execute_lambda(lambda executor: execute_signup_confirmation(executor))
    RewardsDAO(driver=qldb_driver).execute_transaction(lambda dao: execute_signup_confirmation(dao))

    # Confirm the user
    event['response']['autoConfirmUser'] = True

    # Set the email as verified if it is in the request
    if 'email' in event['request']['userAttributes']:
        event['response']['autoVerifyEmail'] = True

    # Set the phone number as verified if it is in the request
    if 'phone_number' in event['request']['userAttributes']:
        event['response']['autoVerifyPhone'] = True

    # Return to Amazon Cognito
    return event


# Enrich logging with contextual information from Lambda
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
# Adding tracer
# See: https://awslabs.github.io/aws-lambda-powertools-python/latest/core/tracer/
@tracer.capture_lambda_handler
# ensures metrics are flushed upon request completion/failure and capturing ColdStart metric
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return signup_confirmation(event=event, context=context)
