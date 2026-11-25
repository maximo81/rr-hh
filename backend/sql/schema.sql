-- =====================================================================
-- Esquema RRHH (PostgreSQL / Neon)
-- Basado en el diagrama ER + casos de uso CU1..CU10 + seguridad (usuarios)
-- Idempotente: se puede ejecutar varias veces.
-- =====================================================================

DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;

-- ---------- Tipos ENUM ----------
CREATE TYPE categoria_puesto   AS ENUM ('directivo', 'jefatura', 'tecnico', 'operativo');
CREATE TYPE estado_posicion    AS ENUM ('vacante', 'ocupada', 'congelada');
CREATE TYPE rol_ocupacion      AS ENUM ('titular', 'interino', 'suplente');
CREATE TYPE rol_usuario        AS ENUM ('admin', 'rrhh', 'evaluador', 'responsable_area');
CREATE TYPE prioridad_nivel    AS ENUM ('baja', 'media', 'alta');
CREATE TYPE estado_accion      AS ENUM ('pendiente', 'en_curso', 'completada', 'cancelada');

-- ---------- Seguridad ----------
CREATE TABLE usuarios (
    id_usuario     SERIAL PRIMARY KEY,
    email          VARCHAR(120) NOT NULL UNIQUE,
    password_hash  VARCHAR(100) NOT NULL,          -- hash bcrypt, nunca texto plano
    rol            rol_usuario  NOT NULL DEFAULT 'rrhh',
    activo         BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_en      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ---------- Estructura organizacional ----------
CREATE TABLE departamentos (
    id_dpto               SERIAL PRIMARY KEY,
    nombre                VARCHAR(80) NOT NULL,
    departamentos_id_dpto INT REFERENCES departamentos(id_dpto)   -- unidad padre (auto-referencia)
);

CREATE TABLE puestos (
    id_puesto             SERIAL PRIMARY KEY,
    codigo                VARCHAR(20)  NOT NULL UNIQUE,
    titulo                VARCHAR(80)  NOT NULL,
    mision                TEXT,
    departamentos_id_dpto INT NOT NULL REFERENCES departamentos(id_dpto)
);

CREATE TABLE especificacion_puesto (
    id_esp_puesto         SERIAL PRIMARY KEY,
    experiencia_necesaria TEXT,
    puestos_id_puesto     INT NOT NULL REFERENCES puestos(id_puesto) ON DELETE CASCADE,
    categoria             categoria_puesto NOT NULL,
    especificacion_puestocol VARCHAR(80)       -- educación formal requerida
);

CREATE TABLE posicion (
    id_posicion        SERIAL PRIMARY KEY,
    puestos_id_puesto  INT NOT NULL REFERENCES puestos(id_puesto),
    localizacion_fisica VARCHAR(80),
    estado             estado_posicion NOT NULL DEFAULT 'vacante'
);

-- ---------- Personas ----------
CREATE TABLE empleados (
    id_empleado   SERIAL PRIMARY KEY,
    legajo        INT          NOT NULL UNIQUE,
    nombre        VARCHAR(60)  NOT NULL,
    apellido      VARCHAR(60)  NOT NULL,
    documento     VARCHAR(40)  NOT NULL UNIQUE,
    email         VARCHAR(120),
    fecha_ingreso DATE         NOT NULL
);

CREATE TABLE ocupacion_puesto (
    posicion_id_posicion INT NOT NULL REFERENCES posicion(id_posicion) ON DELETE CASCADE,
    empleados_id_empleado INT NOT NULL REFERENCES empleados(id_empleado) ON DELETE CASCADE,
    rol rol_ocupacion NOT NULL DEFAULT 'titular',
    PRIMARY KEY (posicion_id_posicion, empleados_id_empleado)
);

-- CU1: antecedentes educativos / experiencia laboral
CREATE TABLE antecedentes (
    id_antecedente SERIAL PRIMARY KEY,
    empleados_id_empleado INT NOT NULL REFERENCES empleados(id_empleado) ON DELETE CASCADE,
    tipo        VARCHAR(20) NOT NULL CHECK (tipo IN ('educacion','titulo','experiencia','cambio_laboral')),
    descripcion TEXT NOT NULL,
    fecha       DATE
);

-- ---------- Habilidades / conocimientos ----------
CREATE TABLE habilidades (
    id_habilidad SERIAL PRIMARY KEY,
    descripcion  TEXT NOT NULL UNIQUE
);

CREATE TABLE habilidades_para_puesto (
    habilidades_id_habilidad INT NOT NULL REFERENCES habilidades(id_habilidad) ON DELETE CASCADE,
    especificacion_puesto_id_esp_puesto INT NOT NULL REFERENCES especificacion_puesto(id_esp_puesto) ON DELETE CASCADE,
    PRIMARY KEY (habilidades_id_habilidad, especificacion_puesto_id_esp_puesto)
);

CREATE TABLE empleados_has_habilidades (
    empleados_id_empleado    INT NOT NULL REFERENCES empleados(id_empleado) ON DELETE CASCADE,
    habilidades_id_habilidad INT NOT NULL REFERENCES habilidades(id_habilidad) ON DELETE CASCADE,
    PRIMARY KEY (empleados_id_empleado, habilidades_id_habilidad)
);

CREATE TABLE conocimiento_requerido (
    id_conocimiento SERIAL PRIMARY KEY,
    descripcion     TEXT NOT NULL UNIQUE
);

CREATE TABLE conocimiento_puesto (
    especificacion_puesto_id_esp_puesto INT NOT NULL REFERENCES especificacion_puesto(id_esp_puesto) ON DELETE CASCADE,
    conocimiento_requerido_id_conocimiento INT NOT NULL REFERENCES conocimiento_requerido(id_conocimiento) ON DELETE CASCADE,
    PRIMARY KEY (especificacion_puesto_id_esp_puesto, conocimiento_requerido_id_conocimiento)
);

-- ---------- Competencias ----------
CREATE TABLE tipo_competencia (
    id_tipo     SERIAL PRIMARY KEY,
    descripcion VARCHAR(45) NOT NULL UNIQUE      -- genérica / técnica
);

CREATE TABLE competencias (
    id_competencias SERIAL PRIMARY KEY,
    descripcion     TEXT NOT NULL UNIQUE,
    tipo_competencia_id_tipo INT NOT NULL REFERENCES tipo_competencia(id_tipo)
);

CREATE TABLE empleados_has_competencias (
    empleados_id_empleado INT NOT NULL REFERENCES empleados(id_empleado) ON DELETE CASCADE,
    competencias_id_competencias INT NOT NULL REFERENCES competencias(id_competencias) ON DELETE CASCADE,
    PRIMARY KEY (empleados_id_empleado, competencias_id_competencias)
);

-- ---------- CU3 / CU4 / CU7: evaluaciones ----------
CREATE TABLE evaluaciones_desempeno (
    id_eval_desempeno SERIAL PRIMARY KEY,
    empleados_id_empleado INT NOT NULL REFERENCES empleados(id_empleado) ON DELETE CASCADE,
    evaluador_id_usuario  INT REFERENCES usuarios(id_usuario),
    periodo       VARCHAR(20) NOT NULL,               -- ej. 2026-S1
    puntaje       NUMERIC(4,2) NOT NULL CHECK (puntaje BETWEEN 0 AND 10),
    observaciones TEXT,
    creado_en     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (empleados_id_empleado, periodo)
);

CREATE TABLE evaluaciones_competencia (
    id_eval_competencia SERIAL PRIMARY KEY,
    empleados_id_empleado INT NOT NULL REFERENCES empleados(id_empleado) ON DELETE CASCADE,
    competencias_id_competencias INT NOT NULL REFERENCES competencias(id_competencias),
    evaluador_id_usuario INT REFERENCES usuarios(id_usuario),
    nivel         SMALLINT NOT NULL CHECK (nivel BETWEEN 1 AND 5),   -- escala 1..5
    fecha         DATE NOT NULL DEFAULT CURRENT_DATE,
    observaciones TEXT                                              -- evidencias
);

-- ---------- CU5: necesidades y capacitaciones ----------
CREATE TABLE necesidades_desarrollo (
    id_necesidad SERIAL PRIMARY KEY,
    empleados_id_empleado INT NOT NULL REFERENCES empleados(id_empleado) ON DELETE CASCADE,
    descripcion TEXT NOT NULL,
    motivo      TEXT,
    prioridad   prioridad_nivel NOT NULL DEFAULT 'media',
    creado_en   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE capacitaciones (
    id_capacitacion SERIAL PRIMARY KEY,
    necesidades_id_necesidad INT REFERENCES necesidades_desarrollo(id_necesidad) ON DELETE SET NULL,
    titulo       VARCHAR(120) NOT NULL,
    descripcion  TEXT,
    fecha_inicio DATE,
    fecha_fin    DATE,
    CHECK (fecha_fin IS NULL OR fecha_inicio IS NULL OR fecha_fin >= fecha_inicio)
);

CREATE TABLE capacitacion_participantes (
    capacitaciones_id_capacitacion INT NOT NULL REFERENCES capacitaciones(id_capacitacion) ON DELETE CASCADE,
    empleados_id_empleado INT NOT NULL REFERENCES empleados(id_empleado) ON DELETE CASCADE,
    PRIMARY KEY (capacitaciones_id_capacitacion, empleados_id_empleado)
);

-- ---------- CU8 / CU9: contribuciones e incentivos ----------
CREATE TABLE contribuciones (
    id_contribucion SERIAL PRIMARY KEY,
    titulo      VARCHAR(120) NOT NULL,
    descripcion TEXT,
    fecha       DATE NOT NULL DEFAULT CURRENT_DATE,
    resultados  TEXT,
    registrado_por INT REFERENCES usuarios(id_usuario)
);

CREATE TABLE contribucion_participantes (
    contribuciones_id_contribucion INT NOT NULL REFERENCES contribuciones(id_contribucion) ON DELETE CASCADE,
    empleados_id_empleado INT NOT NULL REFERENCES empleados(id_empleado) ON DELETE CASCADE,
    PRIMARY KEY (contribuciones_id_contribucion, empleados_id_empleado)
);

CREATE TABLE incentivos (
    id_incentivo SERIAL PRIMARY KEY,
    empleados_id_empleado INT NOT NULL REFERENCES empleados(id_empleado) ON DELETE CASCADE,
    contribuciones_id_contribucion INT REFERENCES contribuciones(id_contribucion) ON DELETE SET NULL,
    tipo   VARCHAR(40) NOT NULL,
    motivo TEXT,
    fecha  DATE NOT NULL DEFAULT CURRENT_DATE
);

-- ---------- CU10: planes de desarrollo ----------
CREATE TABLE planes_desarrollo (
    id_plan SERIAL PRIMARY KEY,
    empleados_id_empleado INT NOT NULL REFERENCES empleados(id_empleado) ON DELETE CASCADE,
    objetivo_general TEXT NOT NULL,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE plan_objetivos (
    id_objetivo SERIAL PRIMARY KEY,
    planes_id_plan INT NOT NULL REFERENCES planes_desarrollo(id_plan) ON DELETE CASCADE,
    descripcion TEXT NOT NULL
);

CREATE TABLE plan_acciones (
    id_accion SERIAL PRIMARY KEY,
    planes_id_plan INT NOT NULL REFERENCES planes_desarrollo(id_plan) ON DELETE CASCADE,
    objetivos_id_objetivo INT REFERENCES plan_objetivos(id_objetivo) ON DELETE SET NULL,
    descripcion TEXT NOT NULL,
    responsable VARCHAR(80),
    fecha_prevista DATE,
    estado estado_accion NOT NULL DEFAULT 'pendiente',
    avance_pct SMALLINT NOT NULL DEFAULT 0 CHECK (avance_pct BETWEEN 0 AND 100)
);

-- ---------- Índices ----------
CREATE INDEX idx_puestos_dpto        ON puestos(departamentos_id_dpto);
CREATE INDEX idx_posicion_puesto     ON posicion(puestos_id_puesto);
CREATE INDEX idx_evalcomp_emp_fecha  ON evaluaciones_competencia(empleados_id_empleado, fecha);
CREATE INDEX idx_evalcomp_comp       ON evaluaciones_competencia(competencias_id_competencias);
CREATE INDEX idx_evaldes_emp         ON evaluaciones_desempeno(empleados_id_empleado);
CREATE INDEX idx_necesidad_emp       ON necesidades_desarrollo(empleados_id_empleado);
CREATE INDEX idx_incentivo_emp       ON incentivos(empleados_id_empleado);
CREATE INDEX idx_plan_emp            ON planes_desarrollo(empleados_id_empleado);
