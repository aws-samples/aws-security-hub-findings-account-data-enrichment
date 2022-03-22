## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0
from importlib.metadata import metadata
import json
import os
import logging
from botocore.exceptions import ClientError

from schema.aws.securityhub.securityhubfindingsimported import Marshaller
from schema.aws.securityhub.securityhubfindingsimported import AWSEvent

from .helper import AccountHelper, AwsHelper


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

secHubClient = AwsHelper().get_client('securityhub')

def enrich_finding(account_id, role):
    #clear enrichment text
    note_text = ""

    #create enrichment text
    account_details = AccountHelper.get_account_details(account_id=account_id, role_name=role)
    tags_dict = {}
    logger.debug("account_details: %s ", json.dumps(account_details))
    note_text = note_text + "Account Name: " + account_details['Name']
    note_text = note_text + " OU Name: " + account_details['OUName']
    if account_details["tags"]:
        tag_names = [tag["Key"] for tag in account_details["tags"]]
        tag_values = [tag["Value"] for tag in account_details["tags"]]
        tags_dict = dict(zip(tag_names,tag_values))
        account_details["Tags"] = tags_dict
        tags_string = ', '.join(key + "=" + value for key, value in tags_dict.items())
        note_text = note_text + " Tags: " + tags_string
    tags_dict["AccountName"] = account_details["Name"]
    tags_dict["OU"] = account_details["OUName"]
    tags_dict["findingEnriched"] = 'True'
    if account_details["AlternateContact"]:
        security_contact = " Security Contact Details: Name:{} | Title:{} | Email:{} | Phone {}".format(account_details["AlternateContact"]["Name"],account_details["AlternateContact"]["Title"],account_details["AlternateContact"]["EmailAddress"],account_details["AlternateContact"]["PhoneNumber"])
        note_text = note_text + security_contact
        tags_dict["securityContact"] = security_contact

    logger.info("enrichment complete: %s" , note_text)
    logger.info("enrichment: %s" , json.dumps(tags_dict))
    return note_text,tags_dict

def lambda_handler(event, context):
    status_code = 200
    message ='function complete'
    assume_role_name = os.environ["ORG_ROLE"]
    table_name = os.environ["tableMetaData"]
    #Deserialize event into strongly typed object
    aws_event:AWSEvent = Marshaller.unmarshall(event, AWSEvent)
    enrichment_text = ""
    enrichment_author = "Security Hub - Enrichment Automation"
    enrichment_finding_id = ""
    enrichment_finding_arn = ""
    #log the event
    logger.debug(aws_event)
    finding = aws_event.detail.findings[0]
    #store this Finding's ID, ARN and Account ID
    enrichment_finding_id = finding["Id"]
    enrichment_finding_arn = finding["ProductArn"]
    account_id = str(finding['AwsAccountId'])
    logger.debug("Finding ID: %s " , enrichment_finding_id + " and product arn " + enrichment_finding_arn)
    try:
        #lookup and build the finding note and user defined fields  based on account Id
        enrichment_text, tags_dict = AccountHelper.get_metadata_from_ddb(table_name=table_name, account_id=account_id)
        if(not enrichment_text):
            logger.debug("Data not in DDB, querying account Service")
            enrichment_text, tags_dict = enrich_finding(account_id, assume_role_name)
            logger.debug("Text to post: %s" , enrichment_text)
            logger.debug("User defined Fields %s" , json.dumps(tags_dict))
            try:
                response = AccountHelper.update_metadata_in_ddb(table_name=table_name,account_id=account_id, account_metadata=tags_dict, text=enrichment_text)
                logger.debug("Data updated in DDB {}".format(response))
            except ClientError as error:
                logger.warn(error.response['Error']['Message'])
            except Exception as error:
                logger.warn(error.response['Error']['Message'])
        else:
            logger.debug("Data found in DDB, Not querying account Service")
        #add the note to the finding and add a userDefinedField to use in the event bridge rule and prevent repeat lookups
        response = secHubClient.batch_update_findings(
            FindingIdentifiers=[
                {
                    'Id': enrichment_finding_id,
                    'ProductArn': enrichment_finding_arn
                }
            ],
            Note={
                'Text': enrichment_text,
                'UpdatedBy': enrichment_author
            },
            UserDefinedFields=tags_dict
        )
    except ClientError as error:
        logger.warn(error.response['Error']['Message'])
        status_code = 500
        message = error.response['Error']['Message']
    except Exception as error:
        status_code = 500
        message = "Unexpected Error occured"
    else:
        if response["UnprocessedFindings"]:
            status_code = 500
            message = 'Failed to update finding'
            logger.warning("Failed to update finding %s", response["UnprocessedFindings"])
        else:
            logger.info("successfully posted note to finding: %s" , enrichment_finding_id + "API response: " + str(response))
    return {
        'statusCode': status_code,
        'body': json.dumps(message)
    }
