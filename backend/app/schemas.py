"""Modelos Pydantic de entrada (validación) de la API."""
from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class LoginIn(BaseModel):
    email: str
    password: str


class EmpleadoIn(BaseModel):
    legajo: int
    nombre: str = Field(min_length=1, max_length=60)
    apellido: str = Field(min_length=1, max_length=60)
    documento: str
    email: Optional[str] = None
    fecha_ingreso: date


class AsignacionPuestoIn(BaseModel):
    puestos_id_puesto: int
    localizacion_fisica: Optional[str] = Field(default=None, max_length=80)  # solo si se crea una posición


class AntecedenteIn(BaseModel):
    tipo: Literal["educacion", "titulo", "experiencia", "cambio_laboral"]
    descripcion: str
    fecha: Optional[date] = None


class PosicionIn(BaseModel):
    id_posicion: Optional[int] = None  # None = posición nueva
    localizacion_fisica: Optional[str] = Field(default=None, max_length=80)
    estado: Literal["vacante", "congelada"]  # las ocupadas se gestionan desde Empleados


class PuestoIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    codigo: str = Field(min_length=1, max_length=20)
    titulo: str = Field(min_length=1, max_length=80)
    mision: Optional[str] = None
    departamentos_id_dpto: int
    # Especificación (una por puesto) y sus requisitos
    categoria: Literal["directivo", "jefatura", "tecnico", "operativo"]
    educacion: Optional[str] = Field(default=None, max_length=80)
    experiencia: Optional[str] = None
    habilidades: list[int] = []
    conocimientos: list[int] = []
    posiciones: list[PosicionIn] = []


class EvalDesempenoIn(BaseModel):
    empleados_id_empleado: int
    periodo: str
    puntaje: float = Field(ge=0, le=10)
    observaciones: Optional[str] = None


class EvalCompetenciaIn(BaseModel):
    empleados_id_empleado: int
    competencias_id_competencias: int
    nivel: int = Field(ge=1, le=5)
    fecha: Optional[date] = None
    observaciones: Optional[str] = None


class NecesidadIn(BaseModel):
    empleados_id_empleado: int
    descripcion: str
    motivo: Optional[str] = None
    prioridad: Literal["baja", "media", "alta"] = "media"
    # CU5 step 3: optionally assign an existing training or create a new one
    capacitacion_id: Optional[int] = None
    capacitacion_titulo: Optional[str] = Field(default=None, max_length=120)
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None


class CapacitacionIn(BaseModel):
    necesidades_id_necesidad: Optional[int] = None
    titulo: str
    descripcion: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    participantes: list[int] = []


class ContribucionIn(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    fecha: Optional[date] = None
    resultados: Optional[str] = None
    participantes: list[int] = []


class IncentivoIn(BaseModel):
    empleados_id_empleado: int
    contribuciones_id_contribucion: Optional[int] = None
    tipo: str
    motivo: Optional[str] = None
    fecha: Optional[date] = None


class AccionIn(BaseModel):
    descripcion: str
    responsable: Optional[str] = None
    fecha_prevista: Optional[date] = None


class PlanIn(BaseModel):
    empleados_id_empleado: int
    objetivo_general: str
    objetivos: list[str] = []
    acciones: list[AccionIn] = []
