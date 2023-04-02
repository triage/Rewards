# Rewards

An attempt to create a Rewards program on AWS SAM.
I once interviewed to be engineering leadership at a bank. The systems design interview was to create a rewards program. I did quite well on the _other_ parts of the virtual on-site. I think I have a much better understanding now about how this could work.

<img width="1350" alt="Screenshot 2023-03-31 at 8 32 17 AM" src="https://user-images.githubusercontent.com/160455/229120949-d81550c8-216f-403d-862d-a361fd86b532.png">

## Requirements:
1. Prevent double-spends (User shouldn't be able to spend more than they have).
2. Populate customer's account with rewards points on creation
3. Allow merchants to authorize redemption of points
4. Allow customers and merchants to see their balances

## Choices:
1. [AWS Quantum Ledger](https://aws.amazon.com/qldb/) for the ledger
  - strongly consistent reads and writes
  - append-only, immutable
  - severless, horizontally scalable, handles our expected throughput
  - [optimistically concurrent](https://docs.aws.amazon.com/qldb/latest/developerguide/concurrency.html)
2. Lambda / SAM
3. Cognito user pools
4. Double-entry accounting

## Preventing double-spends:
1. [AWS Lambda Powertools for Python](https://awslabs.github.io/aws-lambda-powertools-python/2.9.1/utilities/idempotency/) - Idempotency control
- Backed by dynamoDB, strongly-consistent reads
2. Perform QLDB Transaction:
 - Get balance
 - fail if amount greater than balance
 - proceed if less than or equal to balance
 - update balance
 - insert transaction
 
3. __In case of simultaneous transcations:__ QLDB will fail the second transaction in the case that the mutations from first invalides the select on the second.
4. Second will retry and fail if balance is less than the amount



