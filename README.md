# WithSecure Events Collector

Creado por INNOVARE para la recolección de eventos de WithSecure para la
plataforma iSIEM

Multi-tenant **WithSecure Security Events Collector** diseñado para entornos **SOC / SIEM empresariales**, con soporte para:
- despliegue vía **RPM**
- ejecución como **servicio systemd**
- **hot-reload** de configuración
- **rate-limit por tenant**
- **graceful shutdown**
- logging compatible con **journald + archivos**
- aislamiento mediante **Python venv**

---

## Características principales

- Recolección de eventos desde **WithSecure Elements API**
- Multi-cliente (multi-tenant)
- Paginación automática (200 eventos por request)
- Persistencia de estado por cliente
- Intervalo configurable por cliente (base para billing)
- Hot-reload de `config.yml` sin reiniciar el servicio
- Rate-limit independiente por cliente
- Graceful shutdown (SIGTERM)
- Logs estructurados y compatibles con systemd
- Empaquetado como **RPM firmado**
- Listo para integración con SIEM (Wazuh / OpenSearch / Elastic)

---

## Estructura del proyecto

```text
withsecure-collector/
├── collector/
│   ├── main.py               # Orquestador principal
│   ├── api_client.py         # Lógica de consumo API
│   ├── authentication.py    # OAuth2 WithSecure
│   ├── save_events.py       # Escritura JSONL por cliente
│   ├── state.py              # Persistencia de estado
│   ├── logger.py             # Logging centralizado
│   └── config_loader.py      # Carga y validación de config
├── config.yml                # Configuración principal
├── requirements.txt
├── systemd/
│   └── withsecure-collector.service
└── README.md

---

## Descarga y Ejecución

```text
# mkdir /opt/innovare
# cd /opt/innovare
# git clone https://github.com/innovare/withsecure-collector.git
# source venv/Scripts/activate
# export DEBUG=1 # Sólo si se quiere hacer Debug y DEBUG=0 para desactivar
# python3 -m collector.main
