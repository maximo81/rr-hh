"""CU3 Evaluar desempeño y CU4 Evaluar competencias."""
from fastapi import APIRouter, Depends
from ..db import fetch_all, get_cursor
from ..deps import get_current_user, require_roles
from ..schemas import EvalCompetenciaIn, EvalDesempenoIn

router = APIRouter(prefix="/evaluaciones", tags=["evaluaciones"], dependencies=[Depends(get_current_user)])
EVAL = Depends(require_roles("rrhh", "evaluador"))


@router.get("/desempeno")
def listar_desempeno(empleado_id: int | None = None):
    return fetch_all(
        """SELECT ed.*, e.nombre, e.apellido FROM evaluaciones_desempeno ed
           JOIN empleados e ON e.id_empleado = ed.empleados_id_empleado
           WHERE (%s::int IS NULL OR ed.empleados_id_empleado = %s) ORDER BY ed.creado_en DESC LIMIT 200""",
        (empleado_id, empleado_id))


@router.post("/desempeno", status_code=201)
def crear_desempeno(data: EvalDesempenoIn, user: dict = EVAL):
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO evaluaciones_desempeno (empleados_id_empleado, evaluador_id_usuario, periodo, puntaje, observaciones)
               VALUES (%s,%s,%s,%s,%s) RETURNING *""",
            (data.empleados_id_empleado, user["id_usuario"], data.periodo, data.puntaje, data.observaciones))
        return cur.fetchone()


@router.get("/competencias")
def listar_competencias(empleado_id: int | None = None):
    return fetch_all(
        """SELECT ec.*, e.nombre, e.apellido, c.descripcion AS competencia
           FROM evaluaciones_competencia ec
           JOIN empleados e ON e.id_empleado = ec.empleados_id_empleado
           JOIN competencias c ON c.id_competencias = ec.competencias_id_competencias
           WHERE (%s::int IS NULL OR ec.empleados_id_empleado = %s) ORDER BY ec.fecha DESC, ec.id_eval_competencia DESC LIMIT 200""",
        (empleado_id, empleado_id))


@router.post("/competencias", status_code=201)
def crear_competencia(data: EvalCompetenciaIn, user: dict = EVAL):
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO evaluaciones_competencia
               (empleados_id_empleado, competencias_id_competencias, evaluador_id_usuario, nivel, fecha, observaciones)
               VALUES (%s,%s,%s,%s,COALESCE(%s, CURRENT_DATE),%s) RETURNING *""",
            (data.empleados_id_empleado, data.competencias_id_competencias, user["id_usuario"],
             data.nivel, data.fecha, data.observaciones))
        return cur.fetchone()
