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
    "LATERAL_MOVEMENT": "Movimiento Lateral",
    "CREDENTIAL_THEFT": "Robo de Credenciales",
    "CC_NETWORK_CONNECTION": "Comando y Control",
    "ABNORMAL_NETWORK_CONNECTION": "Conexión de Red Anormal",
    "MALWARE": "Malware",
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
