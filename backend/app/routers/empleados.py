"""CU1 Gestionar personas + CU7 historial de competencias."""
from fastapi import APIRouter, Depends, HTTPException
from ..db import fetch_all, fetch_one, get_cursor
from ..deps import get_current_user, require_roles
from ..schemas import AntecedenteIn, AsignacionPuestoIn, EmpleadoIn

router = APIRouter(prefix="/empleados", tags=["empleados"], dependencies=[Depends(get_current_user)])
RRHH = Depends(require_roles("rrhh"))


@router.get("")
def listar(q: str | None = None, limit: int = 100, offset: int = 0):
    like = f"%{q}%" if q else "%"
    return fetch_all(
        """SELECT e.*, p.id_puesto, p.titulo AS puesto, d.nombre AS departamento
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


@router.put("/{id_empleado}/puesto", dependencies=[RRHH])
def asignar_puesto(id_empleado: int, data: AsignacionPuestoIn):
    """Asigna un puesto: libera la posición actual y ocupa una vacante del puesto o crea una nueva."""
    if not fetch_one("SELECT 1 AS x FROM empleados WHERE id_empleado=%s", (id_empleado,)):
        raise HTTPException(404, "Empleado no encontrado")
    if not fetch_one("SELECT 1 AS x FROM puestos WHERE id_puesto=%s", (data.puestos_id_puesto,)):
        raise HTTPException(404, "Puesto no encontrado")
    with get_cursor() as cur:  # una sola transacción: liberar + ocupar
        cur.execute(
            """SELECT o.posicion_id_posicion AS id_posicion, po.puestos_id_puesto AS id_puesto
               FROM ocupacion_puesto o JOIN posicion po ON po.id_posicion = o.posicion_id_posicion
               WHERE o.empleados_id_empleado = %s""", (id_empleado,))
        actuales = cur.fetchall()
        for a in actuales:  # ya ocupa ese puesto: nada que hacer
            if a["id_puesto"] == data.puestos_id_puesto:
                return {"id_posicion": a["id_posicion"], "creada": False}
        cur.execute("DELETE FROM ocupacion_puesto WHERE empleados_id_empleado = %s", (id_empleado,))
        for a in actuales:  # la posición anterior queda vacante si no tiene otro ocupante
            cur.execute(
                """UPDATE posicion SET estado = 'vacante' WHERE id_posicion = %s
                   AND NOT EXISTS (SELECT 1 FROM ocupacion_puesto o WHERE o.posicion_id_posicion = %s)""",
                (a["id_posicion"], a["id_posicion"]))
        cur.execute(
            """SELECT id_posicion FROM posicion WHERE puestos_id_puesto = %s AND estado = 'vacante'
               ORDER BY id_posicion LIMIT 1 FOR UPDATE SKIP LOCKED""", (data.puestos_id_puesto,))
        vacante = cur.fetchone()
        if vacante:
            cur.execute("UPDATE posicion SET estado = 'ocupada' WHERE id_posicion = %s", (vacante["id_posicion"],))
            id_posicion, creada = vacante["id_posicion"], False
        else:
            cur.execute(
                """INSERT INTO posicion (puestos_id_puesto, localizacion_fisica, estado)
                   VALUES (%s, %s, 'ocupada') RETURNING id_posicion""",
                (data.puestos_id_puesto, (data.localizacion_fisica or "").strip() or None))
            id_posicion, creada = cur.fetchone()["id_posicion"], True
        cur.execute("INSERT INTO ocupacion_puesto VALUES (%s, %s, 'titular')", (id_posicion, id_empleado))
    return {"id_posicion": id_posicion, "creada": creada}


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
