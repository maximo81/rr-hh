"""Dependencias de seguridad: usuario autenticado y control de roles (RBAC)."""
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from .db import fetch_one
from .security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED, "Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        raise unauthorized
    user = fetch_one(
        "SELECT id_usuario, email, rol, activo FROM usuarios WHERE id_usuario = %s",
        (int(payload["sub"]),),
    )
    if not user or not user["activo"]:
        raise unauthorized
    return user


def require_roles(*roles: str):
    """Uso: Depends(require_roles('admin','rrhh')). 403 si el rol no alcanza."""
    def checker(user: dict = Depends(get_current_user)) -> dict:
        if user["rol"] != "admin" and user["rol"] not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Permisos insuficientes")
        return user
    return checker
