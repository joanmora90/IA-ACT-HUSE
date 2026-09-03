# Azure Container Apps

Requisitos:

- Azure CLI y extension `containerapp` actualizadas.
- Permiso para crear grupo de recursos, ACR, Log Analytics y Container Apps.
- Aplicacion Entra para la API con scope delegado `user_impersonation`.

Variables:

```bash
export AZURE_SUBSCRIPTION_ID="..."
export ENTRA_TENANT_ID="..."
export ENTRA_API_CLIENT_ID="..."
export DATAVERSE_URL="https://organizacion.crm4.dynamics.com"
export DATAVERSE_CLIENT_ID="..."
export DATAVERSE_CLIENT_SECRET="..."
export AZURE_REGISTRY_NAME="nombreunicoacr"
```

Despliegue:

```bash
./infra/deploy_azure.sh
```

La API valida tokens Entra. En produccion, Power Apps usa los endpoints sin estado de
`/api/v1/power-platform/*`; Dataverse conserva el expediente y la trazabilidad.
