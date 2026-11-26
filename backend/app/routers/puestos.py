"""CU2 Gestionar puestos de trabajo (+ departamentos, competencias, habilidades, conocimientos)."""
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


@router.get("/puestos/codigo-disponible")
def codigo_disponible(codigo: str, excluir: int | None = None):
    """Para validar en el formulario: el código es único (excluir = puesto en edición)."""
    usado = fetch_one(
        "SELECT 1 AS x FROM puestos WHERE codigo = %s AND (%s::int IS NULL OR id_puesto <> %s)",
        (codigo.strip(), excluir, excluir))
    return {"disponible": usado is None}


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
    p["posiciones"] = fetch_all(
        """SELECT po.id_posicion, po.localizacion_fisica, po.estado,
                  string_agg(e.apellido || ', ' || e.nombre, '; ') AS ocupante
           FROM posicion po
           LEFT JOIN ocupacion_puesto o ON o.posicion_id_posicion = po.id_posicion
           LEFT JOIN empleados e ON e.id_empleado = o.empleados_id_empleado
           WHERE po.puestos_id_puesto=%s GROUP BY po.id_posicion ORDER BY po.id_posicion""", (id_puesto,))
    return p


def _guardar_detalle(cur, id_puesto: int, d: PuestoIn):
    """Especificación, habilidades, conocimientos y posiciones editables del puesto (dentro de la transacción)."""
    cur.execute("SELECT id_esp_puesto FROM especificacion_puesto WHERE puestos_id_puesto=%s ORDER BY id_esp_puesto LIMIT 1",
                (id_puesto,))
    esp = cur.fetchone()
    if esp:
        id_esp = esp["id_esp_puesto"]
        cur.execute(
            """UPDATE especificacion_puesto SET categoria=%s, especificacion_puestocol=%s, experiencia_necesaria=%s
               WHERE id_esp_puesto=%s""", (d.categoria, d.educacion or None, d.experiencia or None, id_esp))
    else:
        cur.execute(
            """INSERT INTO especificacion_puesto (puestos_id_puesto, categoria, especificacion_puestocol, experiencia_necesaria)
               VALUES (%s,%s,%s,%s) RETURNING id_esp_puesto""", (id_puesto, d.categoria, d.educacion or None, d.experiencia or None))
        id_esp = cur.fetchone()["id_esp_puesto"]
    # Requisitos: se reemplazan por los marcados
    cur.execute("DELETE FROM habilidades_para_puesto WHERE especificacion_puesto_id_esp_puesto=%s", (id_esp,))
    for h in set(d.habilidades):
        cur.execute("INSERT INTO habilidades_para_puesto VALUES (%s,%s)", (h, id_esp))
    cur.execute("DELETE FROM conocimiento_puesto WHERE especificacion_puesto_id_esp_puesto=%s", (id_esp,))
    for k in set(d.conocimientos):
        cur.execute("INSERT INTO conocimiento_puesto VALUES (%s,%s)", (id_esp, k))
    # Posiciones: las ocupadas no se tocan; las editables que no vienen se eliminan
    ids = [p.id_posicion for p in d.posiciones if p.id_posicion]
    cur.execute(
        """DELETE FROM posicion po WHERE po.puestos_id_puesto=%s AND po.estado <> 'ocupada'
           AND NOT (po.id_posicion = ANY(%s))
           AND NOT EXISTS (SELECT 1 FROM ocupacion_puesto o WHERE o.posicion_id_posicion = po.id_posicion)""",
        (id_puesto, ids))
    for p in d.posiciones:
        if p.id_posicion:
            cur.execute(
                """UPDATE posicion SET localizacion_fisica=%s, estado=%s
                   WHERE id_posicion=%s AND puestos_id_puesto=%s AND estado <> 'ocupada'""",
                (p.localizacion_fisica or None, p.estado, p.id_posicion, id_puesto))
        else:
            cur.execute("INSERT INTO posicion (puestos_id_puesto, localizacion_fisica, estado) VALUES (%s,%s,%s)",
                        (id_puesto, p.localizacion_fisica or None, p.estado))


@router.post("/puestos", status_code=201, dependencies=[Depends(require_roles("rrhh"))])
def crear(data: PuestoIn):
    with get_cursor() as cur:  # una sola transacción: puesto + especificación + requisitos + posiciones
        cur.execute(
            """INSERT INTO puestos (codigo, titulo, mision, departamentos_id_dpto)
               VALUES (%s,%s,%s,%s) RETURNING *""", (data.codigo, data.titulo, data.mision or None, data.departamentos_id_dpto))
        p = cur.fetchone()
        _guardar_detalle(cur, p["id_puesto"], data)
    return p


@router.put("/puestos/{id_puesto}", dependencies=[Depends(require_roles("rrhh"))])
def actualizar(id_puesto: int, data: PuestoIn):
    if not fetch_one("SELECT 1 AS x FROM puestos WHERE id_puesto=%s", (id_puesto,)):
        raise HTTPException(404, "Puesto no encontrado")
    with get_cursor() as cur:
        cur.execute(
            """UPDATE puestos SET codigo=%s, titulo=%s, mision=%s, departamentos_id_dpto=%s
               WHERE id_puesto=%s RETURNING *""",
            (data.codigo, data.titulo, data.mision or None, data.departamentos_id_dpto, id_puesto))
        p = cur.fetchone()
        _guardar_detalle(cur, id_puesto, data)
    return p


@router.get("/competencias")
def competencias():
    return fetch_all(
        """SELECT c.*, t.descripcion AS tipo FROM competencias c
           JOIN tipo_competencia t ON t.id_tipo = c.tipo_competencia_id_tipo ORDER BY c.id_competencias""")


@router.get("/habilidades")
def habilidades():
    return fetch_all("SELECT * FROM habilidades ORDER BY descripcion")


@router.get("/conocimientos")
def conocimientos():
    return fetch_all("SELECT * FROM conocimiento_requerido ORDER BY descripcion")
