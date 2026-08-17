# Vitalis API

Backend del proyecto de grado **UniVita / Vitalis**: aplica el instrumento
**HPLP-II ASD** (52 ítems, 6 dimensiones), calcula los índices con la
metodología **PEPS II** y expone vistas y recomendaciones por rol profesional.

- **Stack:** FastAPI + SQLAlchemy 2.0 + PostgreSQL (Supabase)
- **Frontend:** [UnivitaFrontend](https://github.com/ana21garces/UnivitaFrontend) (Next.js)
- **Repo:** https://github.com/ana21garces/vitalis-api

---

## Arquitectura

Capas en una sola dirección: **endpoint → service → repository → model**.
Un endpoint nunca toca la BD directamente; un repository nunca sabe de HTTP.

```
app/
├── main.py                     # instancia FastAPI, CORS, lifespan, /health
├── api/v1/
│   ├── router.py               # agrega todos los routers bajo /api/v1
│   └── endpoints/              # HTTP: rutas, permisos por rol, códigos de estado
│       ├── auth.py             #   /auth/register, /auth/login
│       └── encuesta_hplp.py    #   /encuesta/** (encuesta, vistas y recomendaciones)
├── core/
│   ├── config.py               # Settings desde .env (pydantic-settings)
│   ├── security.py             # hash de contraseñas + JWT
│   └── dependencies.py         # get_db, get_current_user
├── db/
│   ├── base.py                 # DeclarativeBase
│   ├── session.py              # engine + SessionLocal
│   └── init_db.py              # create_all + migraciones idempotentes al arrancar
├── models/                     # tablas SQLAlchemy
├── schemas/                    # contratos de entrada/salida (Pydantic)
├── repositories/               # queries: todo el SQL vive aquí
└── services/                   # lógica de negocio
    ├── auth_service.py
    ├── encuesta_hplp_service.py       # cálculo de índices PEPS II
    └── recomendaciones_*_service.py   # tablas de tarjetas por rol

scripts/    # utilidades operativas (seed de usuarios profesionales)
migrations/ # schema.sql de referencia
tests/      # pytest sobre SQLite en memoria de archivo
```

### Subescalas del instrumento

Este proyecto usa la **adaptación HPLP-II ASD**, no el HPLP-II original. Los
ítems están redistribuidos: Nutrición tiene 10 (separa proteína vegetal de
animal) y Responsabilidad en Salud tiene 7, en lugar de 9 y 9.

**El prefijo del campo indica la dimensión; el número, la posición de la
pregunta.** `pp_item_19` es el ítem 19 del cuestionario y pertenece a Psicología
Positiva. No aplicar la numeración por módulo 6 del HPLP-II original: mezclaría
ítems entre dimensiones. `tests/unit/` blinda esto.

### Roles

| Rol | Vista que consume |
|---|---|
| `student` | su resultado y sus recomendaciones |
| `capellan` | `/encuesta/capellan/psicologia-positiva` |
| `actividad_fisica` | `/encuesta/actividad-fisica/resultados` |
| `responsabilidad_salud` | `/encuesta/responsabilidad-salud/resultados` |
| `admin` | `/encuesta/admin/resumen`, resetear encuestas |
| `health_manager` | (reservado) solo filtros |

---

## Puesta en marcha

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Copia `.env.example` a `.env` y rellena `SECRET_KEY` y `DATABASE_URL`.
`ALLOWED_ORIGINS` debe incluir la URL del frontend.

```bash
uvicorn app.main:app --reload
```

Docs interactivas en `http://127.0.0.1:8000/docs`.

### Usuarios profesionales

```bash
python -m scripts.seed_roles
```

Crea los usuarios de cada rol profesional que aún no existan. Acepta un rol
concreto como argumento (`python -m scripts.seed_roles capellan`).

La contraseña se genera al azar y **se imprime una sola vez**: guárdala en un
gestor de contraseñas en ese momento. No queda en el código ni en la base de
datos, solo su hash. Para cambiarle la contraseña a un usuario que ya existe:

```bash
python -m scripts.seed_roles --rotar capellan
```

### Recalcular índices

```bash
python -m scripts.recalcular_indices --dry-run
```

Recalcula las columnas derivadas (`*_indice`, `*_nivel`, `puntaje_crudo`,
`indice_global`, `nivel_global`) a partir de los ítems crudos. Solo se necesita
tras cambiar el mapeo de subescalas. Sin `--dry-run` escribe en la BD.

### Tests

```bash
pytest -q
```

Corren contra SQLite, aislados de la BD real. El fixture `client` instancia
`TestClient` **sin** context manager a propósito: el `lifespan` conectaría a
Supabase.

---

## Despliegue

`Procfile` arranca `uvicorn app.main:app`. Al iniciar, `init_db()` crea las
tablas que falten y aplica migraciones idempotentes sobre `users`.
