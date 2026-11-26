"""CU2 Gestionar puestos de trabajo (+ departamentos, competencias, habilidades)."""
from fastapi import APIRouter, Depends, HTTPException
from ..db import fetch_all, fetch_one, get_cursor
from ..deps import get_current_user, require_roles
from ..schemas import PuestoIn

router = APIRouter(tags=["puestos"], dependencies=[Depends(get_current_user)])


@router.get("/departamentos")
def departamentos():
    return fetch_all("SELECT * FROM departamentos ORDER BY id_dpto")


@router.get("/puestos")
def listar():
    return fetch_all(
        """SELECT p.*, d.nombre AS departamento,
                  (SELECT count(*) FROM posicion po WHERE po.puestos_id_puesto = p.id_puesto) AS posiciones,
                  (SELECT count(*) FROM posicion po WHERE po.puestos_id_puesto = p.id_puesto
                     AND po.estado = 'vacante') AS vacantes,
                  (SELECT count(*) FROM posicion po WHERE po.puestos_id_puesto = p.id_puesto
                     AND po.estado = 'ocupada') AS ocupadas
           FROM puestos p JOIN departamentos d ON d.id_dpto = p.departamentos_id_dpto ORDER BY p.codigo""")


@router.get("/puestos/{id_puesto}")
def detalle(id_puesto: int):
    p = fetch_one("SELECT * FROM puestos WHERE id_puesto=%s", (id_puesto,))
    if not p:
        raise HTTPException(404, "Puesto no encontrado")
    p["especificaciones"] = fetch_all("SELECT * FROM especificacion_puesto WHERE puestos_id_puesto=%s", (id_puesto,))
    p["habilidades"] = fetch_all(
        """SELECT DISTINCT h.* FROM habilidades h
           JOIN habilidades_para_puesto hp ON hp.habilidades_id_habilidad = h.id_habilidad
           JOIN especificacion_puesto ep ON ep.id_esp_puesto = hp.especificacion_puesto_id_esp_puesto
           WHERE ep.puestos_id_puesto=%s""", (id_puesto,))
    p["conocimientos"] = fetch_all(
        """SELECT DISTINCT k.* FROM conocimiento_requerido k
           JOIN conocimiento_puesto cp ON cp.conocimiento_requerido_id_conocimiento = k.id_conocimiento
           JOIN especificacion_puesto ep ON ep.id_esp_puesto = cp.especificacion_puesto_id_esp_puesto
           WHERE ep.puestos_id_puesto=%s""", (id_puesto,))
    return p


@router.post("/puestos", status_code=201, dependencies=[Depends(require_roles("rrhh"))])
def crear(data: PuestoIn):
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO puestos (codigo, titulo, mision, departamentos_id_dpto)
               VALUES (%(codigo)s,%(titulo)s,%(mision)s,%(departamentos_id_dpto)s) RETURNING *""", data.model_dump())
        return cur.fetchone()


@router.put("/puestos/{id_puesto}", dependencies=[Depends(require_roles("rrhh"))])
def actualizar(id_puesto: int, data: PuestoIn):
    with get_cursor() as cur:
        cur.execute(
            """UPDATE puestos SET codigo=%(codigo)s, titulo=%(titulo)s, mision=%(mision)s,
               departamentos_id_dpto=%(departamentos_id_dpto)s WHERE id_puesto=%(id)s RETURNING *""",
            {**data.model_dump(), "id": id_puesto})
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Puesto no encontrado")
    return row


@router.get("/competencias")
def competencias():
    return fetch_all(
        """SELECT c.*, t.descripcion AS tipo FROM competencias c
           JOIN tipo_competencia t ON t.id_tipo = c.tipo_competencia_id_tipo ORDER BY c.id_competencias""")


@router.get("/habilidades")
def habilidades():
    return fetch_all("SELECT * FROM habilidades ORDER BY descripcion")
