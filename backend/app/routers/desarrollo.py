"""CU5 necesidades y capacitaciones, CU10 planes de desarrollo."""
from fastapi import APIRouter, Depends, HTTPException
from ..db import fetch_all, fetch_one, get_cursor
from ..deps import get_current_user, require_roles
from ..schemas import CapacitacionIn, NecesidadIn, PlanIn

router = APIRouter(tags=["desarrollo"], dependencies=[Depends(get_current_user)])
RRHH = Depends(require_roles("rrhh"))


@router.get("/necesidades")
def necesidades(empleado_id: int | None = None):
    return fetch_all(
        """SELECT n.*, e.nombre, e.apellido FROM necesidades_desarrollo n
           JOIN empleados e ON e.id_empleado = n.empleados_id_empleado
           WHERE (%s::int IS NULL OR n.empleados_id_empleado = %s)
           ORDER BY CASE n.prioridad WHEN 'alta' THEN 1 WHEN 'media' THEN 2 ELSE 3 END, n.creado_en DESC LIMIT 200""",
        (empleado_id, empleado_id))


@router.post("/necesidades", status_code=201, dependencies=[RRHH])
def crear_necesidad(d: NecesidadIn):
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO necesidades_desarrollo (empleados_id_empleado, descripcion, motivo, prioridad)
               VALUES (%s,%s,%s,%s) RETURNING *""",
            (d.empleados_id_empleado, d.descripcion, d.motivo, d.prioridad))
        return cur.fetchone()


@router.get("/capacitaciones")
def capacitaciones():
    return fetch_all(
        """SELECT c.*, (SELECT count(*) FROM capacitacion_participantes p
                        WHERE p.capacitaciones_id_capacitacion = c.id_capacitacion) AS participantes
           FROM capacitaciones c ORDER BY c.fecha_inicio DESC NULLS LAST""")


@router.post("/capacitaciones", status_code=201, dependencies=[RRHH])
def crear_capacitacion(d: CapacitacionIn):
    with get_cursor() as cur:  # una sola transacción: capacitación + participantes
        cur.execute(
            """INSERT INTO capacitaciones (necesidades_id_necesidad, titulo, descripcion, fecha_inicio, fecha_fin)
               VALUES (%s,%s,%s,%s,%s) RETURNING *""",
            (d.necesidades_id_necesidad, d.titulo, d.descripcion, d.fecha_inicio, d.fecha_fin))
        cap = cur.fetchone()
        for emp in set(d.participantes):
            cur.execute("INSERT INTO capacitacion_participantes VALUES (%s,%s)", (cap["id_capacitacion"], emp))
    return cap


@router.get("/planes")
def planes(empleado_id: int | None = None):
    return fetch_all(
        """SELECT p.*, e.nombre, e.apellido,
                  COALESCE((SELECT round(avg(avance_pct)) FROM plan_acciones a WHERE a.planes_id_plan = p.id_plan),0) AS avance
           FROM planes_desarrollo p JOIN empleados e ON e.id_empleado = p.empleados_id_empleado
           WHERE (%s::int IS NULL OR p.empleados_id_empleado = %s) ORDER BY p.creado_en DESC""",
        (empleado_id, empleado_id))


@router.get("/planes/{id_plan}")
def plan(id_plan: int):
    p = fetch_one("SELECT * FROM planes_desarrollo WHERE id_plan=%s", (id_plan,))
    if not p:
        raise HTTPException(404, "Plan no encontrado")
    p["objetivos"] = fetch_all("SELECT * FROM plan_objetivos WHERE planes_id_plan=%s", (id_plan,))
    p["acciones"] = fetch_all("SELECT * FROM plan_acciones WHERE planes_id_plan=%s ORDER BY fecha_prevista", (id_plan,))
    return p


@router.post("/planes", status_code=201, dependencies=[RRHH])
def crear_plan(d: PlanIn):
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO planes_desarrollo (empleados_id_empleado, objetivo_general) VALUES (%s,%s) RETURNING *",
            (d.empleados_id_empleado, d.objetivo_general))
        pl = cur.fetchone()
        for obj in d.objetivos:
            cur.execute("INSERT INTO plan_objetivos (planes_id_plan, descripcion) VALUES (%s,%s)", (pl["id_plan"], obj))
        for a in d.acciones:
            cur.execute(
                """INSERT INTO plan_acciones (planes_id_plan, descripcion, responsable, fecha_prevista)
                   VALUES (%s,%s,%s,%s)""", (pl["id_plan"], a.descripcion, a.responsable, a.fecha_prevista))
    return pl
