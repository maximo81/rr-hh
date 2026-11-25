"""Punto de entrada FastAPI: CORS, manejo de errores global y routers."""
import logging
from contextlib import asynccontextmanager
import psycopg.errors as pgerr
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .config import settings
from .db import pool
from .routers import auth, contribuciones, dashboard, desarrollo, empleados, evaluaciones, puestos

log = logging.getLogger("rrhh")


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open()          # abre el pool al iniciar
    yield
    pool.close()


app = FastAPI(title="API RRHH", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"], allow_headers=["*"],
)


# ---- Manejo de errores de base de datos (sin filtrar detalles internos) ----
@app.exception_handler(pgerr.UniqueViolation)
async def unique_handler(_: Request, exc):
    return JSONResponse({"detail": "Registro duplicado"}, status_code=409)


@app.exception_handler(pgerr.ForeignKeyViolation)
async def fk_handler(_: Request, exc):
    return JSONResponse({"detail": "Referencia a un registro inexistente o en uso"}, status_code=409)


@app.exception_handler(pgerr.CheckViolation)
async def check_handler(_: Request, exc):
    return JSONResponse({"detail": "Valor fuera de rango permitido"}, status_code=422)


@app.exception_handler(Exception)
async def generic_handler(_: Request, exc: Exception):
    log.exception("Error no controlado")
    return JSONResponse({"detail": "Error interno del servidor"}, status_code=500)


for r in (auth, empleados, puestos, evaluaciones, desarrollo, contribuciones, dashboard):
    app.include_router(r.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
