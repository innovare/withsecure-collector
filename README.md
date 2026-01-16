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

--
## Permisos

```text
- #mkdir /opt/innovare/withsecure-collector/event
- #chown root.wazuh  /opt/innovare/withsecure-collector/events

---

### config.yml

```text

clients:
  - name: innovare
    client_id: xxxx
    client_secret: yyyy
    interval: 300
    output_log: output/innovare.log
    rate_limit_per_minute: 60
    start_mode: fixed
    start_date: "2025-01-01T00:00:00.000Z"

## start_mode define desde qué timestamp inicial el collector empieza a leer eventos cuando arranca el proceso o cuando se añade un cliente nuevo.

Importante:
start_mode solo se aplica una vez por cliente y por ejecución (o tras hot-reload si el cliente es nuevo).
Luego, siempre manda el state guardado.

### start_mode: state (DEFAULT – recomendado)
Qué hace
Lee desde state/<cliente>.json

Si no existe state → usa now
Cuándo usarlo
- Producción normal
- Evitar duplicados
- Continuidad garantizada

Qué hace
- Lee desde state/<cliente>.json
- Si no existe state → usa now

Cuándo usarlo
- Producción normal
- Evitar duplicados
- Continuidad garantizada

### start_mode: now
Qué hace
- Ignora completamente el state
- Empieza desde el momento exacto de arranque

Cuándo usarlo
- Alta de cliente nueva
- No quieres eventos históricos
- Pruebas / PoC

### start_mode: fixed
Qué hace
- Empieza desde una fecha fija (RFC3339)
- Ideal para replay histórico

Cuándo usarlo
- Backfill
- Migraciones
- Carga inicial de SIEM
- Auditorías

Configuración
clients:
  - name: innovare
    client_id: xxx
    client_secret: yyy
    interval: 300
    output_log: output/innovare.log
    start_mode: fixed
    start_date: "2025-01-01T00:00:00.000Z"

Recomendación operativa
Entorno	start_mode
Producción	state
Alta cliente	now
Backfill	fixed
PoC	now

---

## Descarga y Ejecución

```text
- # mkdir /opt/innovare ; cd /opt/innovare
- # chown root:wazuh events
- # cp dev/wazuh/var-ossec-etc-rules/withsecure_rules.xml /var/ossec/etc/rules/
- # cp /var/ossec/etc/ossec.conf /var/ossec/etc/ossec.conf.bak
- # cat dev/wazuh/var-ossec-etc/ossec.conf >> /var/ossec/etc/ossec.conf
- # systemctl restart wazuh-manager
- # git clone https://github.com/innovare/withsecure-collector.git
- # source venv/Scripts/activate
- # export DEBUG=1 # Sólo si se quiere hacer Debug y DEBUG=0 para desactivar
- # python3 -m collector.main

---

