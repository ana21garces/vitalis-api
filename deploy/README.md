# Despliegue

Cómo queda montado Vitalis en el servidor de la universidad, y cómo
reconstruirlo desde cero.

## El entorno

Todo corre en `ubuntusrv`, que es también `ingenieria.unac.edu.co`
(192.168.51.107). El PostgreSQL está en esa misma máquina, no es remoto.

| | Ruta | Puerto |
|---|---|---|
| Backend | `~/univita/vitalis-api` | 8001 |
| Frontend | `~/univita/UnivitaFrontend` | 3001 |
| Base de datos | PostgreSQL local, base `univita` | 5432 |

Ambos escuchan solo en `127.0.0.1`: quedan detrás del proxy del servidor, que
los publica bajo `/~ana.garces/univita`.

### Restricciones a tener en cuenta

Son las que condicionan todo lo demás:

- **No hay sudo.** Por eso los servicios son de usuario (`systemctl --user`) y
  no unidades de sistema.
- **PostgreSQL anterior a la 13.** No existe `gen_random_uuid()` ni la
  extensión `pgcrypto`, y crearla necesitaría superusuario. Por eso los
  scripts generan los UUID en Python.
- **Python 3.10.**

## Instalación

### 1. Código y dependencias

```bash
git clone https://github.com/ana21garces/vitalis-api.git ~/univita/vitalis-api
cd ~/univita/vitalis-api
python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt
```

Copia `.env.example` a `.env` y rellena `SECRET_KEY`, `DATABASE_URL` y
`ALLOWED_ORIGINS` (que debe incluir la URL pública del frontend).

Comprueba que el entorno quedó bien antes de seguir:

```bash
venv/bin/python -m pytest -q
```

Los tests corren contra SQLite y no tocan la base de datos real, así que es
seguro ejecutarlos en el servidor.

### 2. Servicios

`linger` es lo que permite que los servicios de usuario sigan vivos tras
cerrar sesión y arranquen solos al reiniciar la máquina:

```bash
loginctl enable-linger $USER
```

```bash
mkdir -p ~/.config/systemd/user
cp deploy/*.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now vitalis-api univita-frontend
```

Verifica:

```bash
systemctl --user list-units 'univita*' 'vitalis*' --no-pager
curl -s http://127.0.0.1:8001/health
```

Ambos llevan `Restart=always`, así que se levantan solos si se caen. Para
comprobarlo de verdad:

```bash
pkill -9 -u $USER -f "uvicorn app.main:app"; sleep 8
curl -s -o /dev/null -w "api:%{http_code}\n" http://127.0.0.1:8001/health
```

Un `api:200` confirma que systemd lo revivió.

### 3. Usuarios profesionales

```bash
venv/bin/python -m scripts.seed_roles
```

Crea un usuario por rol (admin, capellán, actividad física, responsabilidad en
salud). **La contraseña se genera al azar y se imprime una sola vez**:
guárdala en un gestor de contraseñas en ese momento. Para cambiársela a un
usuario que ya existe:

```bash
venv/bin/python -m scripts.seed_roles --rotar capellan
```

## Operación

### Actualizar

Un `git pull` no surte efecto por sí solo: no hay `--reload`, así que el
proceso sigue con el código viejo en memoria hasta que se reinicie.

```bash
cd ~/univita/vitalis-api && git pull
systemctl --user restart vitalis-api
tail -20 ~/univita/vitalis-api.log
```

En el log deben aparecer las migraciones de `init_db` al arrancar. Si no
salen, el servicio no llegó a levantar bien.

### Respaldo

Antes de cualquier cambio que escriba en la base de datos:

```bash
pg_dump -h ingenieria.unac.edu.co -U univita_user -d univita > ~/univita/respaldo_$(date +%F).sql
```

Comprueba que terminó completo, no solo que el archivo pese:

```bash
tail -3 ~/univita/respaldo_$(date +%F).sql
```

Debe terminar en `-- PostgreSQL database dump complete`.

### Logs

```bash
tail -f ~/univita/vitalis-api.log
tail -f ~/univita/frontend.log
```

Los `print()` de arranque llevan `flush=True` a propósito: con la salida
redirigida a un archivo se quedaban en buffer y el log no mostraba si las
migraciones habían corrido.
