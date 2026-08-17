"""
Genera el reporte de usuarios y sus resultados HPLP-II en CSV.

    python -m scripts.reporte_usuarios                    # -> reporte_usuarios.csv
    python -m scripts.reporte_usuarios ~/univita/rep.csv  # ruta explicita

Incluye una fila por usuario encuestable (se excluyen las cuentas
profesionales y de administracion, que no responden la encuesta), con su
encuesta mas reciente si la completo.

Los indices salen de las columnas ya calculadas en la base de datos, asi que
el reporte refleja el mapeo de subescalas vigente. Si se cambia ese mapeo, hay
que correr scripts.recalcular_indices antes de regenerar el reporte.
"""
import argparse
import csv
import sys

from sqlalchemy import func

from app.db.session import SessionLocal
from app.models.encuesta_hplp import EncuestaHplp
from app.models.user import User, UserRole
from app.services.encuesta_hplp_service import SUBSCALES_HPLP2

# Cuentas del sistema: no responden la encuesta, no van en el reporte.
ROLES_EXCLUIDOS = [
    UserRole.ADMIN.value,
    UserRole.CAPELLAN.value,
    UserRole.ACTIVIDAD_FISICA.value,
    UserRole.RESPONSABILIDAD_SALUD.value,
    UserRole.HEALTH_MANAGER.value,
]

# Nombre legible de cada dimension, en el orden en que salen las columnas.
DIMENSIONES = {
    "relaciones_interpersonales": "relaciones_interpersonales",
    "nutricion": "nutricion",
    "responsabilidad_salud": "responsabilidad_salud",
    "actividad_fisica": "actividad_fisica",
    "manejo_estres": "manejo_estres",
    "psicologia_positiva": "psicologia_positiva",
}

CAMPOS_BASE = [
    "nombre", "email", "facultad", "programa", "tipo_usuario",
    "verificado", "hizo_hplp", "fecha_respuesta",
    "puntaje_crudo", "indice_global", "nivel_global",
]


def columnas() -> list[str]:
    """Cabecera del CSV: campos base mas indice y nivel de cada dimension."""
    cols = list(CAMPOS_BASE)
    for nombre in DIMENSIONES.values():
        cols += [f"{nombre}_indice", f"{nombre}_nivel"]
    return cols


def fila(usuario: User, encuesta: EncuestaHplp | None) -> dict:
    """Construye la fila de un usuario. Sin encuesta, las metricas van vacias."""
    datos = {
        "nombre": usuario.full_name,
        "email": usuario.email,
        "facultad": usuario.facultad or "",
        "programa": usuario.program or "",
        "tipo_usuario": usuario.tipo_usuario or "",
        "verificado": "SI" if usuario.is_verified else "NO",
        "hizo_hplp": "SI" if encuesta else "NO",
        "fecha_respuesta": encuesta.fecha_respuesta if encuesta else "",
        "puntaje_crudo": encuesta.puntaje_crudo if encuesta else "",
        "indice_global": encuesta.indice_global if encuesta else "",
        "nivel_global": encuesta.nivel_global if encuesta else "",
    }

    for dim, nombre in DIMENSIONES.items():
        prefijo, _ = SUBSCALES_HPLP2[dim]
        datos[f"{nombre}_indice"] = getattr(encuesta, f"{prefijo}_indice") if encuesta else ""
        datos[f"{nombre}_nivel"] = getattr(encuesta, f"{prefijo}_nivel") if encuesta else ""

    return datos


def consultar(db) -> list[tuple[User, EncuestaHplp | None]]:
    """Cada usuario encuestable con su encuesta mas reciente, o None."""
    ultimas = (
        db.query(
            EncuestaHplp.usuario_id,
            func.max(EncuestaHplp.id).label("ultimo_id"),
        )
        .group_by(EncuestaHplp.usuario_id)
        .subquery()
    )

    return (
        db.query(User, EncuestaHplp)
        .outerjoin(ultimas, ultimas.c.usuario_id == User.id)
        .outerjoin(EncuestaHplp, EncuestaHplp.id == ultimas.c.ultimo_id)
        .filter(User.role.notin_(ROLES_EXCLUIDOS))
        .order_by(User.full_name)
        .all()
    )


def main(destino: str) -> None:
    db = SessionLocal()
    try:
        filas = consultar(db)
    finally:
        db.close()

    # utf-8-sig para que Excel muestre bien los acentos al abrir el archivo.
    with open(destino, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columnas())
        writer.writeheader()
        for usuario, encuesta in filas:
            writer.writerow(fila(usuario, encuesta))

    completaron = sum(1 for _, e in filas if e)
    total = len(filas)
    tasa = round(completaron / total * 100, 1) if total else 0.0

    print(f"[OK] {destino}")
    print(f"     {total} usuarios, {completaron} con encuesta ({tasa}% de participacion)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "destino", nargs="?", default="reporte_usuarios.csv",
        help="ruta del CSV a generar (por defecto reporte_usuarios.csv)",
    )
    try:
        main(parser.parse_args().destino)
    except OSError as e:
        print(f"No se pudo escribir el archivo: {e}")
        sys.exit(1)
