"""CU6 Analizar evolución del capital humano: indicadores agregados."""
from fastapi import APIRouter, Depends
from ..db import fetch_all, fetch_one
from ..deps import require_roles

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(require_roles("rrhh"))])


@router.get("/kpis")
def kpis():
    totales = fetch_one(
        """SELECT (SELECT count(*) FROM empleados) AS empleados,
                  (SELECT count(*) FROM puestos) AS puestos,
                  (SELECT count(*) FROM evaluaciones_desempeno) + (SELECT count(*) FROM evaluaciones_competencia) AS evaluaciones,
                  (SELECT count(*) FROM necesidades_desarrollo) AS necesidades,
                  (SELECT count(*) FROM capacitaciones) AS capacitaciones,
                  (SELECT count(*) FROM contribuciones) AS contribuciones,
                  (SELECT round(avg(nivel),2) FROM evaluaciones_competencia) AS nivel_promedio""")
    return {
        "totales": totales,
        "evolucion_competencias": fetch_all(
            """SELECT to_char(date_trunc('month', fecha), 'YYYY-MM') AS mes,
                      round(avg(nivel),2)::float AS nivel, count(*) AS evaluaciones
               FROM evaluaciones_competencia GROUP BY 1 ORDER BY 1"""),
        "necesidades_por_prioridad": fetch_all(
            "SELECT prioridad::text AS prioridad, count(*) AS total FROM necesidades_desarrollo GROUP BY 1 ORDER BY 2 DESC"),
        "empleados_por_departamento": fetch_all(
            """SELECT d.nombre AS departamento, count(DISTINCT o.empleados_id_empleado) AS total
               FROM departamentos d
               LEFT JOIN puestos p ON p.departamentos_id_dpto = d.id_dpto
               LEFT JOIN posicion po ON po.puestos_id_puesto = p.id_puesto
               LEFT JOIN ocupacion_puesto o ON o.posicion_id_posicion = po.id_posicion
               GROUP BY d.nombre ORDER BY 2 DESC"""),
        "nivel_por_competencia": fetch_all(
            """SELECT c.descripcion AS competencia, round(avg(ec.nivel),2)::float AS nivel
               FROM evaluaciones_competencia ec JOIN competencias c ON c.id_competencias = ec.competencias_id_competencias
               GROUP BY 1 ORDER BY 2 DESC LIMIT 10"""),
    }
