# collector/normalizers.py
# VERSION: v1.0.0
#
# PURPOSE:
# - Centraliza la normalización de campos semánticos WithSecure
# - Facilita mantenimiento y futuras extensiones
#
# CURRENT NORMALIZERS:
# - details.categories
# - details.risk


# ----------------------------------------------------------------------
# Category normalization (WithSecure -> Español)
# ----------------------------------------------------------------------
CATEGORY_MAP = {
    "ANOMALY": "Anomalía",
    "ABNORMAL_FILE_ACCESSES": "Accesos anormales al archivo",
    "ABNORMAL_NETWORK_CONNECTION": "Conexión de red anormal",
    "ABNORMAL_PROCESS_EXECUTION": "Ejecución anormal del proceso",
    "ABNORMAL_FILE_MODIFICATION": "Modificación anormal del archivo",
    "ABNORMAL_LIBRARY_OR_MODULE": "Biblioteca o módulo anormal",
    "CREDENTIAL_THEFT": "Robo de Credenciales",
    "CC_NETWORK_CONNECTION": "Conexión de red CC",
    "CHANGING_SECURITY_SETTINGS": "Cambio de la configuración de seguridad",
    "CHANGING_FILE_VISIBILITY": "Cambio de visibilidad del archivo",
    "INJECTION_TARGET": "Destino de inyección",
    "INJECTION": "Inyección",
    "LATERAL_MOVEMENT": "Movimiento Lateral",
    "MALWARE": "Malware",
    "PERSISTENCE": "Persistencia",
    "PRIVILEGE_ESCALATION": "Escalamiento de privilegios",
    "RECON_ACTIVITIES": "Actividades de reconocimiento",
    "SCRIPTING_ABUSE": "Abuso de scripting",
    "SYSTEM_OR_TOOL_MISUSE": "Uso incorrecto del sistema o la herramienta",
    "SENSOR_TAMPER": "Manipulación de sensor",
}


def normalize_categories(value):
    """
    Normaliza los valores del campo details.categories.
    Soporta string o lista.
    """
    if isinstance(value, list):
        return [CATEGORY_MAP.get(v, v) for v in value]

    if isinstance(value, str):
        return CATEGORY_MAP.get(value, value)

    return value


# ----------------------------------------------------------------------
# Risk normalization (WithSecure -> Español)
# ----------------------------------------------------------------------
RISK_MAP = {
    "CRITICAL": "Crítico",
    "SEVERE": "Grave",
    "HIGH": "Alto",
    "MEDIUM": "Medio",
    "LOW": "Bajo",
    "INFO": "Informativo",
}


def normalize_risk(value):
    """
    Normaliza el valor del campo details.risk.
    """
    if isinstance(value, str):
        return RISK_MAP.get(value, value)

    return value
