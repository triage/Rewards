# Rewards

An attempt to create a Rewards program on AWS SAM

## Requirements:
1. Prevent double-spends
2. Populate customer's account with rewards points on creation
3. Allow partners to authorize redemption of points
4. Allow customers and partners to see their balances

## Choices:
1. [AWS Quantum Ledger](https://aws.amazon.com/qldb/) for the ledger
  - strongly consistent reads and writes
  - append-only, immutable
  - severless, horizontally scalable, handles our expected throughput
2. Lambda
3. Cognito user pools

## Preventing double-spends:
1. [AWS Lambda Powertools for Python](https://awslabs.github.io/aws-lambda-powertools-python/2.9.1/utilities/idempotency/) - Idempotency control
  1. Backed by dynamoDB, strongly-consistent reads
2. QLDB
  1. Transaction: get balance, fail if amount greater than balance, proceed if less than or equal to balance
  2. QLDB will fail the second transaction in the case that the mutations from first invalides the select on the second
  3. Second will retry and fail if balance is less than the amount

<img width="1131" alt="Screenshot 2023-03-09 at 10 29 10 AM" src="https://user-images.githubusercontent.com/160455/224056206-af012f95-5876-4ba9-8d7c-7b6f1506aa39.png">
