# Sistema RRHH – Gestión del capital humano por competencias

Base de datos PostgreSQL (Neon) + API REST (FastAPI) + dashboard (React/Vite).
Basado en el *Manual de Organización, Descripción y Especificación de Puestos* (RNPN) y los casos de uso CU1–CU10.

## Estructura

```
RRHH/
├── backend/
│   ├── sql/schema.sql        # DDL (27 tablas)
│   ├── scripts/init_db.py    # crea el esquema (¡borra datos!)
│   ├── scripts/seed.py       # puebla con randomuser.me + catálogo del manual
│   ├── app/                  # API FastAPI (routers, seguridad JWT, db)
│   ├── .env                  # secretos (NO se sube a git)
│   └── requirements.txt
└── frontend/                 # React + Vite + Recharts
```

## Requisitos
- Python 3.11+ y Node.js 18+
- Una base PostgreSQL en Neon

## Configuración

1. Copia `backend/.env.example` a `backend/.env` y completa:
   ```
   DATABASE_URL=postgresql://USER:PASSWORD@HOST/neondb?sslmode=require
   JWT_SECRET=un-secreto-largo-aleatorio
   JWT_EXPIRE_MINUTES=60
   CORS_ORIGINS=http://localhost:5173
   ```
2. Backend:
   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe scripts\init_db.py   # crea tablas
   .\.venv\Scripts\python.exe scripts\seed.py      # carga datos
   ```
3. Frontend:
   ```powershell
   cd frontend
   npm install
   ```
   `frontend/.env` contiene `VITE_API_URL=http://localhost:8000`.

## Ejecutar

| Servicio | Comando | URL |
|---|---|---|
| Backend | `cd backend; .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload` | http://localhost:8000/docs |
| Frontend | `cd frontend; npm run dev` | http://localhost:5173 |

Para ver los datos: consola de Neon → **Tables** o **SQL Editor**.

## Usuarios de demostración

| Email | Contraseña | Rol |
|---|---|---|
| admin@rrhh.local | Admin123! | admin |
| rrhh@rrhh.local | Rrhh123! | rrhh |
| evaluador@rrhh.local | Eval123! | evaluador |
| area@rrhh.local | Area123! | responsable_area |

Son solo para desarrollo: cámbialas antes de usar el sistema en serio.

## Seguridad

- Contraseñas con **bcrypt**; sesión con **JWT** (HS256, 60 min).
- `POST /auth/login` devuelve **401** ante credenciales inválidas; **403** si el rol no alcanza.
- Los secretos viven solo en `.env` (ignorado por git).

### Permisos por rol

| Sección / caso de uso | admin | rrhh | evaluador | responsable_area |
|---|:-:|:-:|:-:|:-:|
| Dashboard e indicadores (CU6) | ✔ | ✔ | | |
| Empleados y puestos – consulta (CU1, CU2, CU7) | ✔ | ✔ | ✔ | ✔ |
| Empleados y puestos – alta/edición | ✔ | ✔ | | |
| Evaluar desempeño y competencias (CU3, CU4) | ✔ | ✔ | ✔ | |
| Necesidades, capacitaciones, planes – alta (CU5, CU10) | ✔ | ✔ | | |
| Contribuciones – alta (CU8) | ✔ | ✔ | | ✔ |
| Incentivos – alta (CU9) | ✔ | ✔ | | |

## Endpoints principales

`/auth/login`, `/empleados`, `/empleados/{id}/puesto`, `/puestos`, `/competencias`, `/evaluaciones/{desempeno|competencias}`,
`/necesidades`, `/capacitaciones`, `/planes`, `/contribuciones`, `/incentivos`, `/dashboard/kpis`.
Documentación completa en `/docs`.
