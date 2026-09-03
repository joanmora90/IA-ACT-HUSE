# Microsoft Entra ID

## Registro de la API

1. Crear una aplicacion de tenant unico `AI Act Validator API`.
2. Definir el URI `api://<API_CLIENT_ID>`.
3. Exponer el scope delegado `user_impersonation` para usuarios y administradores.
4. Configurar `accessTokenAcceptedVersion` en `2`.
5. Autorizar solo grupos corporativos aprobados mediante Enterprise Applications.

## Registro cliente del Custom Connector

1. Crear una segunda aplicacion `AI Act Validator Connector`.
2. Añadir el redirect URI que muestra el Custom Connector al guardarlo.
3. Añadir permiso delegado al scope `user_impersonation` de la API.
4. Conceder consentimiento de administrador.
5. Crear un secreto con rotacion corporativa y guardarlo en la conexion del conector.

## Valores de despliegue

- `ENTRA_TENANT_ID`: ID del tenant.
- `ENTRA_AUDIENCE`: `api://<API_CLIENT_ID>`.
- Custom Connector Resource URL: `api://<API_CLIENT_ID>`.

