"""CU8 iniciativas/contribuciones y CU9 incentivos."""
from fastapi import APIRouter, Depends
from ..db import fetch_all, get_cursor
from ..deps import get_current_user, require_roles
from ..schemas import ContribucionIn, IncentivoIn

router = APIRouter(tags=["contribuciones"], dependencies=[Depends(get_current_user)])


@router.get("/contribuciones")
def listar():
    return fetch_all(
        """SELECT c.*, COALESCE(string_agg(e.nombre || ' ' || e.apellido, ', '), '') AS participantes
           FROM contribuciones c
           LEFT JOIN contribucion_participantes cp ON cp.contribuciones_id_contribucion = c.id_contribucion
           LEFT JOIN empleados e ON e.id_empleado = cp.empleados_id_empleado
           GROUP BY c.id_contribucion ORDER BY c.fecha DESC""")


@router.post("/contribuciones", status_code=201)
def crear(d: ContribucionIn, user: dict = Depends(require_roles("rrhh", "responsable_area"))):
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO contribuciones (titulo, descripcion, fecha, resultados, registrado_por)
               VALUES (%s,%s,COALESCE(%s, CURRENT_DATE),%s,%s) RETURNING *""",
            (d.titulo, d.descripcion, d.fecha, d.resultados, user["id_usuario"]))
        c = cur.fetchone()
        for emp in set(d.participantes):
            cur.execute("INSERT INTO contribucion_participantes VALUES (%s,%s)", (c["id_contribucion"], emp))
    return c


@router.get("/incentivos")
def incentivos():
    return fetch_all(
        """SELECT i.*, e.nombre, e.apellido, c.titulo AS contribucion
           FROM incentivos i JOIN empleados e ON e.id_empleado = i.empleados_id_empleado
           LEFT JOIN contribuciones c ON c.id_contribucion = i.contribuciones_id_contribucion
           ORDER BY i.fecha DESC""")


@router.post("/incentivos", status_code=201, dependencies=[Depends(require_roles("rrhh"))])
def crear_incentivo(d: IncentivoIn):
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO incentivos (empleados_id_empleado, contribuciones_id_contribucion, tipo, motivo, fecha)
               VALUES (%s,%s,%s,%s,COALESCE(%s, CURRENT_DATE)) RETURNING *""",
            (d.empleados_id_empleado, d.contribuciones_id_contribucion, d.tipo, d.motivo, d.fecha))
        return cur.fetchone()
