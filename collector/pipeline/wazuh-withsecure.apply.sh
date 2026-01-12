#!/bin/bash

OPENSEARCH_URL="https://localhost:9200"
USER="admin"
PASS="admin"

echo "==> Creando / actualizando Index Template"
curl -k -s -u $USER:$PASS \
  -X PUT "$OPENSEARCH_URL/_index_template/wazuh-alerts-server-timestamp" \
  -H "Content-Type: application/json" \
  -d @wazuh-index-template-withsecure.json

echo ""
echo "==> Creando / actualizando Ingest Pipeline"
curl -k -s -u $USER:$PASS \
  -X PUT "$OPENSEARCH_URL/_ingest/pipeline/wazuh-server-timestamp" \
  -H "Content-Type: application/json" \
  -d @wazuh-ingest-pipeline-withsecure.json

echo ""
echo "==> Verificando recursos"

#echo "- Pipeline:"
#curl -k -s -u $USER:$PASS \
#  "$OPENSEARCH_URL/_ingest/pipeline/wazuh-server-timestamp"

echo ""
echo "- Index Template:"
curl -k -s -u $USER:$PASS \
  "$OPENSEARCH_URL/_index_template/wazuh-alerts-server-timestamp"

echo ""
echo "Provisioning completado."
