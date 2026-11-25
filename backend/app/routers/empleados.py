"""CU1 Gestionar personas + CU7 historial de competencias."""
from fastapi import APIRouter, Depends, HTTPException
from ..db import fetch_all, fetch_one, get_cursor
from ..deps import get_current_user, require_roles
from ..schemas import AntecedenteIn, EmpleadoIn

router = APIRouter(prefix="/empleados", tags=["empleados"], dependencies=[Depends(get_current_user)])
RRHH = Depends(require_roles("rrhh"))


@router.get("")
def listar(q: str | None = None, limit: int = 100, offset: int = 0):
    like = f"%{q}%" if q else "%"
    return fetch_all(
        """SELECT e.*, p.titulo AS puesto, d.nombre AS departamento
           FROM empleados e
           LEFT JOIN ocupacion_puesto o ON o.empleados_id_empleado = e.id_empleado
           LEFT JOIN posicion po ON po.id_posicion = o.posicion_id_posicion
           LEFT JOIN puestos p ON p.id_puesto = po.puestos_id_puesto
           LEFT JOIN departamentos d ON d.id_dpto = p.departamentos_id_dpto
           WHERE e.nombre ILIKE %s OR e.apellido ILIKE %s OR e.documento ILIKE %s
           ORDER BY e.apellido, e.nombre LIMIT %s OFFSET %s""",
        (like, like, like, min(limit, 500), offset),
    )


@router.get("/{id_empleado}")
def detalle(id_empleado: int):
    emp = fetch_one("SELECT * FROM empleados WHERE id_empleado = %s", (id_empleado,))
    if not emp:
        raise HTTPException(404, "Empleado no encontrado")
    emp["antecedentes"] = fetch_all(
        "SELECT * FROM antecedentes WHERE empleados_id_empleado = %s ORDER BY fecha DESC NULLS LAST", (id_empleado,))
    emp["habilidades"] = fetch_all(
        """SELECT h.* FROM habilidades h JOIN empleados_has_habilidades eh
           ON eh.habilidades_id_habilidad = h.id_habilidad WHERE eh.empleados_id_empleado = %s""", (id_empleado,))
    return emp


@router.post("", status_code=201, dependencies=[RRHH])
def crear(data: EmpleadoIn):
    with get_cursor() as cur:  # UniqueViolation -> 409 (handler global)
        cur.execute(
            """INSERT INTO empleados (legajo, nombre, apellido, documento, email, fecha_ingreso)
               VALUES (%(legajo)s, %(nombre)s, %(apellido)s, %(documento)s, %(email)s, %(fecha_ingreso)s)
               RETURNING *""", data.model_dump())
        return cur.fetchone()


@router.put("/{id_empleado}", dependencies=[RRHH])
def actualizar(id_empleado: int, data: EmpleadoIn):
    with get_cursor() as cur:
        cur.execute(
            """UPDATE empleados SET legajo=%(legajo)s, nombre=%(nombre)s, apellido=%(apellido)s,
               documento=%(documento)s, email=%(email)s, fecha_ingreso=%(fecha_ingreso)s
               WHERE id_empleado=%(id)s RETURNING *""", {**data.model_dump(), "id": id_empleado})
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Empleado no encontrado")
    return row


@router.post("/{id_empleado}/antecedentes", status_code=201, dependencies=[RRHH])
def agregar_antecedente(id_empleado: int, data: AntecedenteIn):
    if not fetch_one("SELECT 1 AS x FROM empleados WHERE id_empleado=%s", (id_empleado,)):
        raise HTTPException(404, "Empleado no encontrado")
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO antecedentes (empleados_id_empleado, tipo, descripcion, fecha)
               VALUES (%s,%s,%s,%s) RETURNING *""",
            (id_empleado, data.tipo, data.descripcion, data.fecha))
        return cur.fetchone()


@router.get("/{id_empleado}/historial-competencias")
def historial_competencias(id_empleado: int):
    """CU7: evaluaciones de competencias ordenadas cronológicamente."""
    return fetch_all(
        """SELECT ec.fecha, c.descripcion AS competencia, ec.nivel, ec.observaciones
           FROM evaluaciones_competencia ec
           JOIN competencias c ON c.id_competencias = ec.competencias_id_competencias
           WHERE ec.empleados_id_empleado = %s ORDER BY ec.fecha, c.descripcion""", (id_empleado,))
