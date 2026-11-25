"""Autenticación: valida credenciales contra la tabla usuarios (Neon) y devuelve JWT."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from ..db import fetch_one
from ..deps import get_current_user
from ..schemas import LoginIn
from ..security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

# Hash ficticio para igualar tiempos de respuesta cuando el email no existe (anti user-enumeration)
_DUMMY = "$2b$12$C6UzMDM.H6dfI/f/IKcEeO5T1Qn9vN7yZb1y5nq0tqZ3x8m0eJ1WK"


def _authenticate(email: str, password: str) -> dict:
    user = fetch_one("SELECT * FROM usuarios WHERE lower(email) = lower(%s)", (email,))
    ok = verify_password(password, user["password_hash"] if user else _DUMMY)
    if not user or not ok or not user["activo"]:
        # Mensaje genérico: no revela si falló el email o la contraseña
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def _token_response(user: dict) -> dict:
    return {
        "access_token": create_access_token(user["id_usuario"], user["email"], user["rol"]),
        "token_type": "bearer",
        "rol": user["rol"],
        "email": user["email"],
    }


@router.post("/login")
def login(data: LoginIn):
    """Login JSON (usado por el frontend React)."""
    return _token_response(_authenticate(data.email, data.password))


@router.post("/token")
def token(form: OAuth2PasswordRequestForm = Depends()):
    """Login form-data (botón Authorize de Swagger /docs)."""
    return _token_response(_authenticate(form.username, form.password))


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return user
