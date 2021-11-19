#!/bin/bash
if [[ $# -lt 1 ]] ; then
     echo "Please specify the region as the arguement eg: ./create-bucket.sh us-east-1"
     exit
else
     REGION=$1
fi
BUCKET_ID=$(dd if=/dev/random bs=8 count=1 2>/dev/null | od -An -tx1 | tr -d ' \t\n')
BUCKET_NAME=lambda-artifacts-$BUCKET_ID
PROFILE=$(cat profile.txt)
echo $BUCKET_NAME > bucket-name.txt
aws s3 mb s3://$BUCKET_NAME  --profile $PROFILE --region $REGION
