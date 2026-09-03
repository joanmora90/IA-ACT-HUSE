@description('Nombre de la Container App')
param appName string = 'ai-act-validator'

@description('Region de Azure')
param location string = resourceGroup().location

@description('Imagen completa, incluido tag')
param image string

@description('Servidor del registro, por ejemplo example.azurecr.io')
param registryServer string

@description('Usuario del registro')
param registryUsername string

@secure()
@description('Contrasena del registro')
param registryPassword string

@description('Tenant de Microsoft Entra ID')
param entraTenantId string

@description('Audience de la API, normalmente api://<client-id>')
param entraAudience string

@description('URL base del entorno Dataverse')
param dataverseUrl string

@description('Client ID del principal de servicio con acceso de lectura a tablas juridicas')
param dataverseClientId string

@secure()
@description('Secreto del principal de servicio de Dataverse')
param dataverseClientSecret string

param rulesetId string = 'EU_AI_ACT_2026_07_27_V0_1'

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${appName}-logs'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource environment 'Microsoft.App/managedEnvironments@2025-07-01' = {
  name: '${appName}-env'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listKeys().primarySharedKey
      }
    }
  }
}

resource api 'Microsoft.App/containerApps@2025-07-01' = {
  name: appName
  location: location
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
      }
      secrets: [
        {
          name: 'registry-password'
          value: registryPassword
        }
        {
          name: 'dataverse-client-secret'
          value: dataverseClientSecret
        }
      ]
      registries: [
        {
          server: registryServer
          username: registryUsername
          passwordSecretRef: 'registry-password'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: image
          env: [
            { name: 'APP_ENV', value: 'production' }
            { name: 'AUTH_MODE', value: 'entra' }
            { name: 'ENTRA_TENANT_ID', value: entraTenantId }
            { name: 'ENTRA_AUDIENCE', value: entraAudience }
            { name: 'RULESET_ID', value: rulesetId }
            { name: 'RULE_SOURCE', value: 'dataverse' }
            { name: 'DATAVERSE_URL', value: dataverseUrl }
            { name: 'DATAVERSE_TENANT_ID', value: entraTenantId }
            { name: 'DATAVERSE_CLIENT_ID', value: dataverseClientId }
            { name: 'DATAVERSE_CLIENT_SECRET', secretRef: 'dataverse-client-secret' }
            { name: 'DATABASE_PATH', value: '/tmp/ai_act_validator.db' }
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 8000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 10
              periodSeconds: 30
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: 8000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 5
              periodSeconds: 10
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 3
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

output fqdn string = api.properties.configuration.ingress.fqdn
output url string = 'https://${api.properties.configuration.ingress.fqdn}'
