# Custom Connector

Generar el Swagger 2.0 importable cuando existan el host de Azure, el tenant y el
identificador de la aplicacion Entra de la API:

```bash
python scripts/render_custom_connector.py \
  --host ai-act-validator.example.azurecontainerapps.io \
  --tenant-id 00000000-0000-0000-0000-000000000000 \
  --api-client-id 00000000-0000-0000-0000-000000000000
```

Importar `apiDefinition.swagger.json` dentro de la solucion de Power Platform.

Seguridad del conector:

- Tipo: OAuth 2.0.
- Proveedor: Microsoft Entra ID.
- Resource URL: `api://<API_CLIENT_ID>`.
- Scope: `api://<API_CLIENT_ID>/user_impersonation`.
- Activar `on-behalf-of login` si lo exige la politica del tenant.

El archivo usa OpenAPI 2.0, formato requerido por Custom Connectors.

