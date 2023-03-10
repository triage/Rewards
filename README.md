# Rewards

An attempt to create a Rewards program on AWS SAM.
I once interviewed to be engineering leadership at a bank. The systems design interview was to create a rewards program. I did quite well on the _other_ parts of the virtual on-site. I think I have a much better understanding now about how this could work.

## Requirements:
1. Prevent double-spends (User shouldn't be able to spend more than they have).
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
- Backed by dynamoDB, strongly-consistent reads
2. Perform QLDB Transaction:
 - Get balance
 - fail if amount greater than balance
 - proceed if less than or equal to balance
 - update balance
 - insert transaction
 
3. In case of simultaneous transcations: QLDB will fail the second transaction in the case that the mutations from first invalides the select on the second
4. Second will retry and fail if balance is less than the amount

<img width="1401" alt="Screenshot 2023-03-09 at 3 15 32 PM" src="https://user-images.githubusercontent.com/160455/224130969-03866fc2-097a-457f-ba5c-8d70e5768857.png">
