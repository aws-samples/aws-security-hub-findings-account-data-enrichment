#!/bin/bash
set -eo pipefail
ARTIFACT_BUCKET=$(cat bucket-name.txt)
TEMPLATE=aws-securityhub-findings-resource-enrichment.yaml
PROFILE=$(cat profile.txt)
sam build -t $TEMPLATE
cd .aws-sam/build

sam package --debug  --profile $PROFILE --region us-west-2 --s3-bucket $ARTIFACT_BUCKET --output-template-file aws-securityhub-findings-resource-enrichment-cf.yml
sam deploy --debug --profile $PROFILE --region us-west-2 --template-file aws-securityhub-findings-resource-enrichment-cf.yml --stack-name aws-securityhub-findings-enrichment-stack --capabilities CAPABILITY_NAMED_IAM
