# collector/authentication.py
# VERSION: v1.3.0
# FIX:
# - Restored correct Basic Auth header
# - Base64(client_id:client_secret)
# - Compatible with WithSecure OAuth2

import logging
import requests
from base64 import b64encode

log = logging.getLogger(__name__)

TOKEN_URL = "https://api.connect.withsecure.com/as/token.oauth2"

class WithSecureAuth:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._token = None

    def authenticate(self) -> str:
        if self._token:
            return self._token

        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = b64encode(credentials.encode("utf-8")).decode("utf-8")

        headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": "innovare-siem-collector"
        }

        data = {
            "grant_type": "client_credentials",
            "scope": "connect.api.read"
        }

        response = requests.post(TOKEN_URL, headers=headers, data=data)

        if not response.ok:
            log.error("Authentication failed: %s", response.text)
            raise RuntimeError("WithSecure authentication failed")

        self._token = response.json()["access_token"]
        log.debug("Authentication successful")
        return self._token
