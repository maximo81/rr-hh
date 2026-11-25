"""Puebla la BD: personas desde la API externa randomuser.me + catálogos del manual RNPN.
Ejecutar tras init_db.py. Es re-ejecutable (vacía las tablas antes)."""
import random
import sys
from datetime import date, timedelta
from pathlib import Path

import httpx
import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import settings  # noqa: E402
from app.security import hash_password  # noqa: E402

random.seed(42)

# ---------------- Catálogos (Manual de Organización, Dirección de Informática) ----------------
DEPARTAMENTOS = [  # (nombre, índice del padre)
    ("Dirección de Informática", None),
    ("Unidad de Administración de Redes y Recursos Informáticos", 0),
    ("Unidad de Procesamiento de Partidas", 0),
    ("Unidad de Administración de Base de Datos", 0),
    ("Unidad de Desarrollo de Aplicaciones", 0),
]

# (codigo, titulo, dpto_idx, categoria, educacion, experiencia, nº de posiciones, misión)
PUESTOS = [
    ("DI-01", "Director de Informática", 0, "directivo", "Ingeniero o Lic. en Sistemas Informáticos", "5 años en puestos similares", 1, "Administrar, coordinar, dirigir y supervisar los sistemas informáticos estratégicos de la institución."),
    ("RE-01", "Jefe de Administración de Redes y Recursos Informáticos", 1, "jefatura", "Graduado en Sistemas con énfasis en redes", "2 años en puestos similares", 1, "Administrar hardware y software de la infraestructura informática."),
    ("RE-02", "Técnico de Soporte Informático", 1, "tecnico", "Técnico o estudiante de Ingeniería en Sistemas", "2 años en puestos similares", 3, "Mantenimiento preventivo y correctivo y soporte a usuarios."),
    ("PP-01", "Jefe de la Unidad de Procesamiento de Partidas", 2, "jefatura", "Licenciado en Ciencias Jurídicas", "2 años en puestos similares", 1, "Supervisar la actualización de la base de datos del estado familiar."),
    ("PP-02", "Coordinador del Área de Recolección", 2, "jefatura", "Estudiante de 3er año de Ciencias Jurídicas", "2 años en puestos similares", 1, "Coordinar la recolección de partidas en los Registros del Estado Familiar."),
    ("PP-03", "Recolector", 2, "operativo", "Estudios universitarios en Ciencias Jurídicas", "2 años en puestos similares", 8, "Recolectar partidas de nacimiento y defunción en las alcaldías."),
    ("PP-04", "Coordinador del Área Técnica de Supervisión", 2, "jefatura", "Técnico Programador Analista", "2 años en puestos similares", 1, "Soporte técnico de aplicativos y control de producción."),
    ("PP-05", "Analista Informático", 2, "tecnico", "Técnico en Informática o estudiante de 3er año", "2 años en puestos similares", 3, "Alimentar la base de datos y dar control de calidad."),
    ("PP-06", "Coordinador del Área de Procesamiento de Partidas", 2, "jefatura", "Licenciado en Ciencias Jurídicas", "2 años en puestos similares", 1, "Supervisar y dar seguimiento a la actualización de la base de datos."),
    ("PP-07", "Colaborador Jurídico", 2, "tecnico", "Estudiante de 3er año de Ciencias Jurídicas", "2 años en puestos similares", 7, "Verificar la calidad de los datos indexados de partidas."),
    ("PP-08", "Operador", 2, "operativo", "Estudiante de 3er año de Ciencias Jurídicas", "2 años en puestos similares", 3, "Filtrar y verificar el indexamiento de datos."),
    ("PP-09", "Digitador", 2, "operativo", "Bachiller o secretaria", "2 años en puestos similares", 20, "Digitar y verificar partidas de nacimiento y defunción."),
    ("PP-10", "Supervisor", 2, "jefatura", "Lic. en Administración de Empresas", "2 años en puestos similares", 1, "Supervisar el escaneo de partidas."),
    ("PP-11", "Escaneador", 2, "operativo", "Bachiller o secretaria", "2 años en puestos similares", 6, "Escanear partidas de nacimiento y defunción."),
    ("BD-01", "Jefe de la Unidad de Administración de Base de Datos", 3, "jefatura", "Lic. o Ing. en Sistemas Informáticos", "2 años en puestos similares", 1, "Operación y administración de las bases de datos del equipo central."),
    ("BD-02", "Coordinador del Help Desk", 3, "jefatura", "Licenciado en Ciencias Jurídicas, abogado o notario", "2 años en puestos similares", 1, "Coordinar al Help Desk que atiende los Duicentros."),
    ("BD-03", "Colaborador Jurídico del Help Desk", 3, "tecnico", "Licenciado en Ciencias Jurídicas, abogado o notario", "2 años en puestos similares", 1, "Atender solicitudes de los delegados y aprobar o denegar incidencias."),
    ("DA-01", "Jefe de la Unidad de Desarrollo de Aplicaciones", 4, "jefatura", "Ingeniería o Licenciatura en Sistemas", "2 años en puestos similares", 1, "Planificar y ejecutar el desarrollo de aplicativos."),
    ("DA-02", "Programador Analista", 4, "tecnico", "Técnico, Licenciatura o Ingeniería en Sistemas", "2 años en puestos similares", 2, "Análisis, diseño, desarrollo y mantenimiento de sistemas."),
    ("DA-03", "Técnico de Soporte en Sitio Central", 4, "tecnico", "Técnico Informático o estudiante de 3er año", "2 años en puestos similares", 1, "Soporte de equipos del centro de cómputo central."),
]

HABILIDADES = ["Trabajo en equipo", "Comunicación oral y escrita", "Capacidad de análisis y síntesis", "Liderazgo",
               "Toma de decisiones", "Orientación al cliente", "Discreción y confidencialidad", "Proactividad e innovación",
               "Ofimática", "Agilidad de digitación", "Trabajo bajo presión", "Inglés técnico"]

CONOCIMIENTOS = ["Bases de datos relacionales", "Oracle / Oracle Developer", "Redes y comunicaciones", "Seguridad informática",
                 "Sistemas operativos (AIX, Windows, UNIX)", "Leyes registrales y familiares", "Ordenamiento jurídico salvadoreño",
                 "Análisis y diseño de sistemas", "Hardware y software de equipos", "Servidores web (Tomcat, Apache)"]

# Conocimientos por título de puesto (palabras clave) -> índices en CONOCIMIENTOS
CONOC_POR_AREA = {0: [7, 0, 3], 1: [2, 3, 4, 8], 2: [5, 6, 0], 3: [0, 1, 3], 4: [1, 7, 9, 0]}

TIPOS = ["Genérica", "Técnica"]
COMPETENCIAS = [
    ("Trabajo en equipo", 0), ("Comunicación oral y escrita", 0), ("Orientación al cliente", 0), ("Liderazgo", 0),
    ("Toma de decisiones", 0), ("Ética profesional", 0), ("Confidencialidad en el manejo de información", 0), ("Innovación", 0),
    ("Administración de bases de datos", 1), ("Diseño de redes y topología", 1), ("Seguridad informática", 1),
    ("Desarrollo de aplicaciones", 1), ("Aplicación de leyes registrales", 1), ("Soporte técnico de hardware y software", 1),
]

CAPACITACIONES = ["Seguridad informática avanzada", "Liderazgo y gestión de equipos", "Oracle Developer", "Normativa registral vigente",
                  "Inglés técnico", "Atención al ciudadano", "Administración de redes"]

LOCALIZACIONES = ["Torre RNPN - Piso 1", "Torre RNPN - Piso 2", "Torre RNPN - Piso 3", "Centro de cómputo central", "Duicentro Metropolitano"]


def fetch_people(n: int) -> list[dict]:
    """API externa randomuser.me; si falla, genera nombres locales para no bloquear el seed."""
    try:
        r = httpx.get("https://randomuser.me/api/", params={"results": n, "nat": "es", "inc": "name,email,dob,id,registered", "seed": "rrhh"}, timeout=30)
        r.raise_for_status()
        return r.json()["results"]
    except Exception as exc:  # noqa: BLE001
        print(f"AVISO: randomuser.me no disponible ({exc}); usando datos locales")
        nombres = ["Ana", "Luis", "María", "Carlos", "Sofía", "Jorge", "Lucía", "Pedro"]
        apellidos = ["Gómez", "Pérez", "Rivas", "Flores", "Mejía", "Castro", "Ortiz", "Molina"]
        return [{"name": {"first": random.choice(nombres), "last": random.choice(apellidos)}, "email": f"user{i}@example.com",
                 "id": {"value": None}, "registered": {"date": "2020-01-01T00:00:00Z"}} for i in range(n)]


def main():
    total_pos = sum(p[6] for p in PUESTOS)
    people = fetch_people(total_pos)

    with psycopg.connect(settings.database_url) as conn, conn.cursor() as cur:
        def ins(sql, params=()):
            cur.execute(sql, params)   # el SQL incluye RETURNING <id>
            return cur.fetchone()[0]

        # Vaciar todo (orden irrelevante con CASCADE)
        cur.execute("""TRUNCATE usuarios, departamentos, puestos, empleados, habilidades, conocimiento_requerido,
                       tipo_competencia, contribuciones, capacitaciones, necesidades_desarrollo RESTART IDENTITY CASCADE""")

        # Usuarios (contraseñas bcrypt). Solo datos de demo.
        demo = [("admin@rrhh.local", "Admin123!", "admin"), ("rrhh@rrhh.local", "Rrhh123!", "rrhh"),
                ("evaluador@rrhh.local", "Eval123!", "evaluador"), ("area@rrhh.local", "Area123!", "responsable_area")]
        uids = {}
        for email, pw, rol in demo:
            uids[rol] = ins("INSERT INTO usuarios (email,password_hash,rol) VALUES (%s,%s,%s) RETURNING id_usuario",
                            (email, hash_password(pw), rol))

        # Departamentos
        dpto_ids = []
        for nombre, padre in DEPARTAMENTOS:
            dpto_ids.append(ins("INSERT INTO departamentos (nombre, departamentos_id_dpto) VALUES (%s,%s) RETURNING id_dpto",
                                (nombre, dpto_ids[padre] if padre is not None else None)))

        hab_ids = [ins("INSERT INTO habilidades (descripcion) VALUES (%s) RETURNING id_habilidad", (h,)) for h in HABILIDADES]
        con_ids = [ins("INSERT INTO conocimiento_requerido (descripcion) VALUES (%s) RETURNING id_conocimiento", (k,)) for k in CONOCIMIENTOS]
        tipo_ids = [ins("INSERT INTO tipo_competencia (descripcion) VALUES (%s) RETURNING id_tipo", (t,)) for t in TIPOS]
        comp_ids = [ins("INSERT INTO competencias (descripcion, tipo_competencia_id_tipo) VALUES (%s,%s) RETURNING id_competencias",
                        (d, tipo_ids[t])) for d, t in COMPETENCIAS]

        # Puestos, especificaciones, requisitos (cada puesto requiere al menos una habilidad)
        posiciones = []  # (id_posicion, dpto_idx)
        for cod, tit, di, cat, edu, exp, n, mision in PUESTOS:
            pid = ins("INSERT INTO puestos (codigo,titulo,mision,departamentos_id_dpto) VALUES (%s,%s,%s,%s) RETURNING id_puesto",
                      (cod, tit, mision, dpto_ids[di]))
            esp = ins("""INSERT INTO especificacion_puesto (experiencia_necesaria, puestos_id_puesto, categoria, especificacion_puestocol)
                         VALUES (%s,%s,%s,%s) RETURNING id_esp_puesto""", (exp, pid, cat, edu))
            for h in random.sample(hab_ids, 3):
                cur.execute("INSERT INTO habilidades_para_puesto VALUES (%s,%s)", (h, esp))
            for k in CONOC_POR_AREA[di]:
                cur.execute("INSERT INTO conocimiento_puesto VALUES (%s,%s)", (esp, con_ids[k]))
            for _ in range(n):
                posiciones.append((ins("INSERT INTO posicion (puestos_id_puesto, localizacion_fisica, estado) VALUES (%s,%s,'ocupada') RETURNING id_posicion",
                                       (pid, random.choice(LOCALIZACIONES))), di))
        # Algunas posiciones vacantes (sin ocupante) para los KPI
        for _ in range(4):
            cur.execute("INSERT INTO posicion (puestos_id_puesto, localizacion_fisica, estado) VALUES (1,%s,'vacante')", (random.choice(LOCALIZACIONES),))

        # Empleados (API externa) + ocupación + habilidades + competencias
        emp_ids = []
        for i, (person, (pos_id, _)) in enumerate(zip(people, posiciones), start=1):
            doc = person.get("id", {}).get("value") or f"{random.randint(10000000, 99999999)}-{random.randint(0, 9)}"
            ingreso = person.get("registered", {}).get("date", "2020-01-01")[:10]
            eid = ins("""INSERT INTO empleados (legajo,nombre,apellido,documento,email,fecha_ingreso)
                         VALUES (%s,%s,%s,%s,%s,%s) RETURNING id_empleado""",
                      (1000 + i, person["name"]["first"], person["name"]["last"], f"{doc}-{i}", person.get("email"), ingreso))
            emp_ids.append(eid)
            cur.execute("INSERT INTO ocupacion_puesto VALUES (%s,%s,'titular')", (pos_id, eid))
            for h in random.sample(hab_ids, random.randint(2, 4)):
                cur.execute("INSERT INTO empleados_has_habilidades VALUES (%s,%s)", (eid, h))
            for c in random.sample(comp_ids, 4):
                cur.execute("INSERT INTO empleados_has_competencias VALUES (%s,%s)", (eid, c))
            cur.execute("INSERT INTO antecedentes (empleados_id_empleado,tipo,descripcion,fecha) VALUES (%s,'educacion',%s,%s)",
                        (eid, random.choice(["Bachillerato", "Técnico en Informática", "Licenciatura en Ciencias Jurídicas", "Ingeniería en Sistemas"]),
                         date(2005 + random.randint(0, 12), 12, 1)))

        # Evaluaciones de competencias: 3 mediciones por empleado en los últimos 12 meses, tendencia creciente
        hoy = date.today()
        for eid in emp_ids:
            for c in random.sample(comp_ids, 3):
                base = random.randint(1, 3)
                for k, meses in enumerate((11, 6, 1)):
                    nivel = min(5, base + (1 if k and random.random() < 0.6 else 0) + (1 if k == 2 and random.random() < 0.4 else 0))
                    cur.execute("""INSERT INTO evaluaciones_competencia (empleados_id_empleado,competencias_id_competencias,evaluador_id_usuario,nivel,fecha,observaciones)
                                   VALUES (%s,%s,%s,%s,%s,%s)""",
                                (eid, c, uids["evaluador"], nivel, hoy - timedelta(days=30 * meses), "Observación basada en evidencia del período"))
            for periodo in ("2025-S2", "2026-S1"):
                cur.execute("""INSERT INTO evaluaciones_desempeno (empleados_id_empleado,evaluador_id_usuario,periodo,puntaje,observaciones)
                               VALUES (%s,%s,%s,%s,%s)""", (eid, uids["evaluador"], periodo, round(random.uniform(5.5, 9.8), 2), "Cumple con estándares del puesto"))

        # Necesidades de desarrollo + capacitaciones
        nec_ids = []
        for eid in random.sample(emp_ids, 30):
            nec_ids.append((ins("""INSERT INTO necesidades_desarrollo (empleados_id_empleado,descripcion,motivo,prioridad)
                                   VALUES (%s,%s,%s,%s) RETURNING id_necesidad""",
                                (eid, random.choice(CAPACITACIONES), "Brecha detectada en evaluación de competencias",
                                 random.choice(["baja", "media", "media", "alta"]))), eid))
        for titulo in CAPACITACIONES:
            nid, eid = random.choice(nec_ids)
            ini = hoy - timedelta(days=random.randint(0, 150))
            cap = ins("""INSERT INTO capacitaciones (necesidades_id_necesidad,titulo,descripcion,fecha_inicio,fecha_fin)
                         VALUES (%s,%s,%s,%s,%s) RETURNING id_capacitacion""",
                      (nid, titulo, f"Curso de {titulo.lower()}", ini, ini + timedelta(days=14)))
            for p in set(random.sample(emp_ids, 6) + [eid]):
                cur.execute("INSERT INTO capacitacion_participantes VALUES (%s,%s)", (cap, p))

        # Contribuciones e incentivos
        for t in ["Automatización del reporte de producción", "Mejora del proceso de escaneo", "Manual de inducción actualizado", "Optimización de consultas del Help Desk"]:
            cid = ins("""INSERT INTO contribuciones (titulo,descripcion,fecha,resultados,registrado_por)
                         VALUES (%s,%s,%s,%s,%s) RETURNING id_contribucion""",
                      (t, f"Iniciativa: {t}", hoy - timedelta(days=random.randint(10, 300)), "Reducción de tiempos operativos", uids["responsable_area"]))
            part = random.sample(emp_ids, 2)
            for p in part:
                cur.execute("INSERT INTO contribucion_participantes VALUES (%s,%s)", (cid, p))
            cur.execute("INSERT INTO incentivos (empleados_id_empleado,contribuciones_id_contribucion,tipo,motivo) VALUES (%s,%s,%s,%s)",
                        (part[0], cid, random.choice(["Bono", "Día libre", "Reconocimiento público"]), "Aporte destacado"))

        # Planes de desarrollo
        for eid in random.sample(emp_ids, 8):
            pl = ins("INSERT INTO planes_desarrollo (empleados_id_empleado,objetivo_general) VALUES (%s,%s) RETURNING id_plan",
                     (eid, "Nivelar competencias requeridas para el puesto"))
            ob = ins("INSERT INTO plan_objetivos (planes_id_plan,descripcion) VALUES (%s,%s) RETURNING id_objetivo", (pl, "Cerrar brechas de competencias técnicas"))
            for d in ("Capacitación formal", "Práctica supervisada", "Acompañamiento (mentoring)"):
                cur.execute("""INSERT INTO plan_acciones (planes_id_plan,objetivos_id_objetivo,descripcion,responsable,fecha_prevista,estado,avance_pct)
                               VALUES (%s,%s,%s,'Jefe inmediato',%s,%s,%s)""",
                            (pl, ob, d, hoy + timedelta(days=random.randint(15, 120)), random.choice(["pendiente", "en_curso"]), random.choice([0, 25, 50, 75])))
        conn.commit()

        for t in ("usuarios", "empleados", "puestos", "posicion", "evaluaciones_competencia", "necesidades_desarrollo", "capacitaciones"):
            cur.execute(f"SELECT count(*) FROM {t}")
            print(f"{t}: {cur.fetchone()[0]}")
    print("\nUsuarios demo: " + ", ".join(f"{e} / {p}" for e, p, _ in demo))


if __name__ == "__main__":
    main()
