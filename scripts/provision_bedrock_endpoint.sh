#!/usr/bin/env bash
# Provisions the Bedrock VPC interface endpoint for the project (issue #95).
#
# Mirrors this repo's existing provisioning mechanism: raw AWS CLI calls run
# manually by an operator with the correct account/profile, then recorded in
# docs/INVENTORY.md in the same batch (adr-12-ephemeral-run rule 5). There is
# no Terraform/CDK in this repo — see docs/INVENTORY.md for every other
# resource created the same way.
#
# Prerequisites:
#   - AWS CLI configured with a profile that resolves to account 789650504128
#     (profile "kodex", per docs/INVENTORY.md header). Verify first:
#       aws sts get-caller-identity --profile kodex
#   - Region us-east-1 (adr-02-initial-stack).
#
# This script is idempotent-unsafe by design (matches the rest of the repo's
# manual provisioning steps) — run it once, then hand-copy the returned IDs
# into docs/INVENTORY.md, flipping the two "planned" rows to "ephemeral".

set -euo pipefail

PROFILE="${AWS_PROFILE:-kodex}"
REGION="us-east-1"
PROJECT_SLUG="${PROJECT_SLUG:-astro-drf-aws}"
VPC_ID="vpc-0f6c992f8a75a6629"          # alvs-prod, docs/INVENTORY.md
TASK_SG_ID="sg-027b8d1f3fe41007a"        # alvs-prod-task-sg, docs/INVENTORY.md
SUBNET_IDS=(
  "subnet-0367b5e29ffc0c525"            # alvs-prod-pub-1a
  "subnet-03e3ec09d37971485"            # alvs-prod-pub-1b
)
TAGS="Key=project,Value=${PROJECT_SLUG} Key=env,Value=prod Key=lifecycle,Value=ephemeral Key=Name,Value=alvs-prod-bedrock-vpce-sg"
EP_TAGS="Key=project,Value=${PROJECT_SLUG} Key=env,Value=prod Key=lifecycle,Value=ephemeral Key=Name,Value=alvs-prod-bedrock-runtime-vpce"

echo "Caller identity (must be account 789650504128):"
aws sts get-caller-identity --profile "$PROFILE"

echo "Creating security group alvs-prod-bedrock-vpce-sg..."
SG_ID=$(aws ec2 create-security-group \
  --profile "$PROFILE" --region "$REGION" \
  --group-name alvs-prod-bedrock-vpce-sg \
  --description "Ingress 443 from alvs-prod-task-sg for the Bedrock runtime VPC endpoint (issue #95)" \
  --vpc-id "$VPC_ID" \
  --tag-specifications "ResourceType=security-group,Tags=[$TAGS]" \
  --query 'GroupId' --output text)
echo "Created SG: $SG_ID"

aws ec2 authorize-security-group-ingress \
  --profile "$PROFILE" --region "$REGION" \
  --group-id "$SG_ID" \
  --protocol tcp --port 443 \
  --source-group "$TASK_SG_ID"

echo "Creating Bedrock runtime interface endpoint..."
VPCE_ID=$(aws ec2 create-vpc-endpoint \
  --profile "$PROFILE" --region "$REGION" \
  --vpc-id "$VPC_ID" \
  --vpc-endpoint-type Interface \
  --service-name "com.amazonaws.${REGION}.bedrock-runtime" \
  --subnet-ids "${SUBNET_IDS[@]}" \
  --security-group-ids "$SG_ID" \
  --private-dns-enabled \
  --tag-specifications "ResourceType=vpc-endpoint,Tags=[$EP_TAGS]" \
  --query 'VpcEndpoint.VpcEndpointId' --output text)

echo "Created VPC endpoint: $VPCE_ID"
echo
echo "Next step (adr-12 rule 5, same batch): update docs/INVENTORY.md —"
echo "  flip both 'planned' rows to 'ephemeral' with SG=$SG_ID, VPCE=$VPCE_ID."
