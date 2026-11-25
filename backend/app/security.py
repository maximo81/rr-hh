"""Hash de contraseñas (bcrypt) y emisión / validación de tokens JWT."""
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from .config import settings

ALGORITHM = "HS256"


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except ValueError:  # hash malformado
        return False


def create_access_token(user_id: int, email: str, rol: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "email": email, "rol": rol, "exp": exp}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Lanza jwt.PyJWTError si el token es inválido o expiró."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
