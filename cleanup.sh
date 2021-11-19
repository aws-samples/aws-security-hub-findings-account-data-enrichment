#!/bin/bash
set -eo pipefail
STACK=aws-securityhub-findings-enrichment-stack
PROFILE=$(cat profile.txt)
if [[ $# -lt 1 ]] ; then
     echo "Please specify the region as the arguement eg: ./cleanup.sh us-east-1"
     exit
else
     REGION=$1
fi
FUNCTION=$(aws cloudformation describe-stack-resource --profile $PROFILE --stack-name $STACK --logical-resource-id SHEnrichmentFunction --query 'StackResourceDetail.PhysicalResourceId' --output text --region $REGION )
aws cloudformation delete-stack --profile $PROFILE --stack-name $STACK --region $REGION
echo "Deleted $STACK stack."

if [ -f bucket-name.txt ]; then
    ARTIFACT_BUCKET=$(cat bucket-name.txt)
    if [[ ! $ARTIFACT_BUCKET =~ lambda-artifacts-[a-z0-9]{16} ]] ; then
        echo "Bucket was not created by this application. Skipping."
    else
        while true; do
            read -p "Delete deployment artifacts and bucket ($ARTIFACT_BUCKET)? (y/n)" response
            case $response in
                [Yy]* ) aws s3 rb --profile $PROFILE --force s3://$ARTIFACT_BUCKET; rm bucket-name.txt; break;;
                [Nn]* ) break;;
                * ) echo "Response must start with y or n.";;
            esac
        done
    fi
fi

while true; do
    read -p "Delete function log group (/aws/lambda/$FUNCTION)? (y/n)" response
    case $response in
        [Yy]* ) aws logs delete-log-group --profile $PROFILE --region $REGION  --log-group-name /aws/lambda/$FUNCTION; break;;
        [Nn]* ) break;;
        * ) echo "Response must start with y or n.";;
    esac
done

rm -f out.yml out.json
rm -rf build .gradle target
