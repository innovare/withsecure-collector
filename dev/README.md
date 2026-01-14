## Comandos utilizados

# Ver si los LOGs están como alertas
tail -f /var/ossec/logs/alerts/alerts.json

# Ver si los LOGs están ingestándose
tail -f /var/ossec/logs/archives/archives.json

# Reiniciar Wazuh cada vez que se hagan cambios
systemctl restart wazuh-manager

# Hacer pruebas de los Decoders y Rules
/var/ossec/bin/wazuh-logtest

# Analizar los archivos de configuración
/var/ossec/bin/wazuh-analysisd -t

# Añadir mapping
curl -k -u admin:admin -X PUT https://localhost:9200/_index_template/wazuh-alerts-withsecure -H "Content-Type: application/json" -d @wazuh-alerts-withsecure-template.json

# Localtime
sudo timedatectl set-timezone America/Bogota

# test EICAR AMSI
powershell echo '"X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"'

## Verificar que el INDEX TEMPLATE existe (lo primero)
curl -k -u admin:admin \
https://localhost:9200/_index_template/wazuh-alerts-withsecure?pretty


