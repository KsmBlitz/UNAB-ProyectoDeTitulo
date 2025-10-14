# Certificados AWS IoT Core

Coloca aquí tus certificados de AWS IoT Core:

1. **root-CA.crt** - Certificado raíz de Amazon (descargar de: https://www.amazontrust.com/repository/AmazonRootCA1.pem)
2. **device.pem.crt** - Certificado del dispositivo (generado en AWS IoT Core)
3. **private.pem.key** - Clave privada del dispositivo (generado en AWS IoT Core)

## Cómo obtener los certificados:

### 1. En AWS IoT Core Console:
- Ve a **Manage > Things**
- Crea una nueva "Thing" o usa una existente
- Ve a **Security > Certificates**
- Crea un nuevo certificado o usa uno existente
- Descarga los archivos

### 2. Archivos necesarios:
```
certificates/
├── root-CA.crt          # Amazon Root CA 1
├── device.pem.crt       # Tu certificado del dispositivo
└── private.pem.key      # Tu clave privada
```

### 3. Permisos de certificados:
Asegúrate de que el certificado tenga una política que permita:
- `iot:Connect`
- `iot:Subscribe` 
- `iot:Receive`

### 4. Ejemplo de política AWS IoT:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iot:Connect"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow", 
      "Action": [
        "iot:Subscribe",
        "iot:Receive"
      ],
      "Resource": [
        "arn:aws:iot:us-east-1:YOUR_ACCOUNT_ID:topicfilter/sensor/*"
      ]
    }
  ]
}
```

**¡IMPORTANTE!** No subas estos archivos a Git. Están en el .gitignore por seguridad.