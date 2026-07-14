from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time

from fastapi import Header, HTTPException
from pydantic import BaseModel

from mindfolio_api.config import get_settings


class MemberIdentity(BaseModel):
    member_id: str
    display_name: str


def authenticate_invite_code(invite_code: str) -> MemberIdentity | None:
    for candidate, member_id in get_settings().invite_identity_map.items():
        if secrets.compare_digest(invite_code, candidate):
            return MemberIdentity(member_id=member_id, display_name=member_id)
    return None


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def issue_session_token(identity: MemberIdentity) -> str:
    settings = get_settings()
    payload = {
        "member_id": identity.member_id,
        "display_name": identity.display_name,
        "exp": int(time.time()) + settings.session_ttl_hours * 3600,
    }
    encoded_payload = _encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(
        settings.session_secret.encode("utf-8"), encoded_payload.encode("ascii"), hashlib.sha256
    ).digest()
    return f"{encoded_payload}.{_encode(signature)}"


def authenticate_session_token(token: str) -> MemberIdentity | None:
    encoded_payload, separator, encoded_signature = token.partition(".")
    if not separator:
        return None
    settings = get_settings()
    expected = hmac.new(
        settings.session_secret.encode("utf-8"), encoded_payload.encode("ascii"), hashlib.sha256
    ).digest()
    try:
        supplied = _decode(encoded_signature)
        if not hmac.compare_digest(expected, supplied):
            return None
        payload = json.loads(_decode(encoded_payload))
        if not isinstance(payload, dict) or int(payload.get("exp", 0)) <= int(time.time()):
            return None
        member_id = payload.get("member_id")
        display_name = payload.get("display_name")
        if not isinstance(member_id, str) or not member_id:
            return None
        return MemberIdentity(
            member_id=member_id,
            display_name=display_name if isinstance(display_name, str) and display_name else member_id,
        )
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.casefold() != "bearer" or not token:
        return None
    return token


def require_member(authorization: str | None = Header(default=None)) -> MemberIdentity:
    token = _bearer_token(authorization)
    identity = authenticate_session_token(token or "")
    if identity is None:
        raise HTTPException(status_code=401, detail="Invalid or missing member access code.")
    return identity


def optional_member(authorization: str | None = Header(default=None)) -> MemberIdentity | None:
    token = _bearer_token(authorization)
    return authenticate_session_token(token or "") if token else None
