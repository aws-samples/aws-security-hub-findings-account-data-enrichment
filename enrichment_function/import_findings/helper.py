## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

import logging
import boto3
from botocore.client import Config


class AwsHelper:
    def get_client(self, name, aws_region=None):
        config = Config(
            retries = {
                'max_attempts': 5,
                'mode': 'standard'
            }
        )
        if aws_region:
            return boto3.client(name, region_name=aws_region, config=config)
        else:
            return boto3.client(name, config=config)

    def get_resource(self, name, aws_region=None):
        config = Config(
            retries = dict(
                max_attempts = 5
            )
        )

        if aws_region:
            return boto3.resource(name, region_name=aws_region, config=config)
        else:
            return boto3.resource(name, config=config)

    def get_session_for_role(self, role_arn: str):
        role = boto3.client('sts').assume_role(RoleArn=role_arn, RoleSessionName='switch-role')
        credentials = role['Credentials']
        aws_access_key_id = credentials['AccessKeyId']
        aws_secret_access_key = credentials['SecretAccessKey']
        aws_session_token = credentials['SessionToken']
        return boto3.session.Session(
            aws_access_key_id = aws_access_key_id,
            aws_secret_access_key = aws_secret_access_key,
            aws_session_token = aws_session_token)

class AccountHelper:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    @staticmethod
    def get_account_details(account_id, role_name):
        account_details = {}
        organizations_client = AwsHelper().get_client('organizations')
        response = organizations_client.describe_account(AccountId=account_id)
        account_details["Name"] = response["Account"]["Name"]
        response = organizations_client.list_parents(ChildId=account_id)
        ou_id = response["Parents"][0]["Id"]
        if ou_id and response["Parents"][0]["Type"] == "ORGANIZATIONAL_UNIT":
            response = organizations_client.describe_organizational_unit(OrganizationalUnitId=ou_id)
            account_details["OUName"] = response["OrganizationalUnit"]["Name"]
        elif ou_id:
            account_details["OUName"] = "ROOT"
        if role_name:
            account_client = AwsHelper().get_session_for_role(role_name).client("account")
        else:
            account_client = AwsHelper().get_client('account')
        account_details["AlternateContact"] = {}
        try:
            response = account_client.get_alternate_contact(
                AccountId = account_id,
                AlternateContactType = 'SECURITY'
            )
            AccountHelper.logger.debug("Alternate Contact Response: %", str(response))
            if response['AlternateContact']:
                print("contact :{}".format(str(response["AlternateContact"])))
                account_details["AlternateContact"] = response["AlternateContact"]
        except account_client.exceptions.AccessDeniedException as error:
            #Potentially due to calling alternate contact on Org Management account
            AccountHelper.logger.warning(error.response['Error']['Message'])
        except account_client.exceptions.ResourceNotFoundException as exception:
            #When there is no alternate contacts set
            AccountHelper.logger.warning(exception.response['Error']['Message'])

        response = organizations_client.list_tags_for_resource(ResourceId=account_id)
        results = response["Tags"]
        while "NextToken" in response:
            response = organizations_client.list_tags_for_resource(ResourceId=account_id, NextToken=response["NextToken"])
            results.extend(response["Tags"])

        account_details["tags"] = results
        AccountHelper.logger.info("account_details: %s" , str(account_details))
        return account_details
