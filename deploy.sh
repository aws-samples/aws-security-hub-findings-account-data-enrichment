#!/bin/bash
set -eo pipefail
if [[ $# -lt 1 ]] ; then
     echo "Please specify the region as the arguement eg: ./deploy.sh us-east-1"
     exit
else
     REGION=$1
fi
ARTIFACT_BUCKET=$(cat bucket-name.txt)
TEMPLATE=aws-securityhub-findings-resource-enrichment.yaml
PROFILE=$(cat profile.txt)
sam build -t $TEMPLATE
cd .aws-sam/build

sam package --debug  --profile $PROFILE --region $REGION --s3-bucket $ARTIFACT_BUCKET --output-template-file aws-securityhub-findings-resource-enrichment-cf.yml
sam deploy --debug --profile $PROFILE --region $REGION --template-file aws-securityhub-findings-resource-enrichment-cf.yml --stack-name aws-securityhub-findings-enrichment-stack --capabilities CAPABILITY_NAMED_IAM --guided
