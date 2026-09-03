from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Header, HTTPException, status
from jwt import PyJWKClient

from .config import Settings


@dataclass(frozen=True)
class CurrentUser:
    subject: str
    name: str | None = None


class EntraAuthenticator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.jwk_client: PyJWKClient | None = None
        if settings.auth_mode == "entra":
            if not settings.entra_tenant_id or not settings.entra_audience:
                raise RuntimeError("ENTRA_TENANT_ID y ENTRA_AUDIENCE son obligatorios")
            jwks_url = (
                f"https://login.microsoftonline.com/{settings.entra_tenant_id}/discovery/v2.0/keys"
            )
            self.jwk_client = PyJWKClient(jwks_url, cache_keys=True)

    def authenticate(self, authorization: Annotated[str | None, Header()] = None) -> CurrentUser:
        if self.settings.auth_mode == "disabled":
            return CurrentUser(subject="local-development", name="Local developer")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")
        token = authorization.removeprefix("Bearer ").strip()
        try:
            assert self.jwk_client is not None
            signing_key = self.jwk_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.settings.entra_audience,
                issuer=f"https://login.microsoftonline.com/{self.settings.entra_tenant_id}/v2.0",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token no valido"
            ) from exc
        return CurrentUser(subject=claims["sub"], name=claims.get("name"))
