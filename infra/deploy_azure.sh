#!/usr/bin/env bash
set -euo pipefail

: "${AZURE_SUBSCRIPTION_ID:?Define AZURE_SUBSCRIPTION_ID}"
: "${ENTRA_TENANT_ID:?Define ENTRA_TENANT_ID}"
: "${ENTRA_API_CLIENT_ID:?Define ENTRA_API_CLIENT_ID}"
: "${DATAVERSE_URL:?Define DATAVERSE_URL}"
: "${DATAVERSE_CLIENT_ID:?Define DATAVERSE_CLIENT_ID}"
: "${DATAVERSE_CLIENT_SECRET:?Define DATAVERSE_CLIENT_SECRET}"

deployment_location="${AZURE_LOCATION:-westeurope}"
deployment_group="${AZURE_RESOURCE_GROUP:-rg-ai-act-validator}"
container_app_name="${CONTAINER_APP_NAME:-ai-act-validator}"
registry_name="${AZURE_REGISTRY_NAME:-aiactvalidatoracr}"
image_tag="${IMAGE_TAG:-0.1.0}"

az account set --subscription "$AZURE_SUBSCRIPTION_ID"
az group create --name "$deployment_group" --location "$deployment_location" --output none

if ! az acr show --name "$registry_name" --resource-group "$deployment_group" --output none 2>/dev/null; then
  az acr create \
    --name "$registry_name" \
    --resource-group "$deployment_group" \
    --sku Basic \
    --admin-enabled true \
    --output none
fi

az acr build \
  --registry "$registry_name" \
  --image "ai-act-validator:${image_tag}" \
  .

registry_server="$(az acr show --name "$registry_name" --query loginServer --output tsv)"
registry_user="$(az acr credential show --name "$registry_name" --query username --output tsv)"
registry_password="$(az acr credential show --name "$registry_name" --query 'passwords[0].value' --output tsv)"

az deployment group create \
  --resource-group "$deployment_group" \
  --template-file infra/main.bicep \
  --parameters \
    appName="$container_app_name" \
    location="$deployment_location" \
    image="${registry_server}/ai-act-validator:${image_tag}" \
    registryServer="$registry_server" \
    registryUsername="$registry_user" \
    registryPassword="$registry_password" \
    entraTenantId="$ENTRA_TENANT_ID" \
    entraAudience="api://${ENTRA_API_CLIENT_ID}" \
    dataverseUrl="$DATAVERSE_URL" \
    dataverseClientId="$DATAVERSE_CLIENT_ID" \
    dataverseClientSecret="$DATAVERSE_CLIENT_SECRET" \
  --query 'properties.outputs.url.value' \
  --output tsv
