source env.sh

CLIENT_ID=$(aws cognito-idp create-user-pool-client \
  --user-pool-id ${USER_POOL_ID} \
  --client-name rewards-backend \
  --no-generate-secret \
  --explicit-auth-flows ADMIN_NO_SRP_AUTH \
  --query 'UserPoolClient.ClientId' \
  --output text)

echo "User Pool Client created with id ${CLIENT_ID}"
echo "export COGNITO_CLIENT_ID=${CLIENT_ID}" >> env.sh
