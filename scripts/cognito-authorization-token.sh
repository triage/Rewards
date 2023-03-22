aws cognito-idp admin-create-user \
--user-pool-id us-east-1_1KWE8lEIA \
--username peoplefromgoodhomes@gmail.com \
--temporary-password "MyTempPassword1!" \
--user-attributes Name=email,Value=peoplefromgoodhomes@gmail.com Name=given_name,Value=Jackson Name=family_name,Value=Adams \
--desired-delivery-mediums EMAIL

aws cognito-idp admin-set-user-password --user-pool-id us-east-1_1KWE8lEIA --username peoplefromgoodhomes@gmail.com --password NewP@ssword123 --permanent

aws cognito-idp initiate-auth \
    --auth-flow USER_PASSWORD_AUTH \
    --client-id 5k4l0mftbi1ds835ubar5c2ie \
    --auth-parameters USERNAME=peoplefromgoodhomes@gmail.com,PASSWORD=NewP@ssword123