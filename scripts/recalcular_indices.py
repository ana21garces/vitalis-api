"""
Recalcula los índices y niveles de las encuestas ya guardadas.

Necesario una sola vez, tras corregir el mapeo de subescalas en
encuesta_hplp_service: las respuestas crudas (los 52 ítems) siempre se
guardaron bien, pero las columnas *_indice, *_nivel, puntaje_crudo,
indice_global y nivel_global se derivaron del mapeo anterior.

Uso:
    python -m scripts.recalcular_indices --dry-run   # muestra qué cambiaría
    python -m scripts.recalcular_indices             # aplica los cambios
"""
import argparse

from app.db.session import SessionLocal
from app.models.encuesta_hplp import EncuestaHplp
from app.services.encuesta_hplp_service import (
    ITEM_FIELDS,
    SUBSCALES_HPLP2,
    _indice,
    _nivel_global,
    _nivel_por_indice,
)

CAMPOS_DERIVADOS = (
    [f"{prefijo}_indice" for prefijo, _ in SUBSCALES_HPLP2.values()]
    + [f"{prefijo}_nivel" for prefijo, _ in SUBSCALES_HPLP2.values()]
    + ["puntaje_crudo", "indice_global", "nivel_global"]
)


def recalcular(encuesta: EncuestaHplp) -> dict:
    """Devuelve los valores derivados a partir de los ítems crudos de la fila."""
    nuevos: dict = {}

    for prefijo, campos in SUBSCALES_HPLP2.values():
        promedio = sum(getattr(encuesta, c) for c in campos) / len(campos)
        indice = _indice(promedio)
        nuevos[f"{prefijo}_indice"] = indice
        nuevos[f"{prefijo}_nivel"] = _nivel_por_indice(indice)

    puntaje_crudo = sum(getattr(encuesta, c) for c in ITEM_FIELDS)
    nuevos["puntaje_crudo"] = puntaje_crudo
    nuevos["indice_global"] = _indice(puntaje_crudo / len(ITEM_FIELDS))
    nuevos["nivel_global"] = _nivel_global(puntaje_crudo)

    return nuevos


def main(dry_run: bool) -> None:
    db = SessionLocal()
    try:
        encuestas = db.query(EncuestaHplp).order_by(EncuestaHplp.id).all()
        print(f"Encuestas encontradas: {len(encuestas)}")

        con_cambios = 0
        for encuesta in encuestas:
            nuevos = recalcular(encuesta)
            diferencias = {
                campo: (getattr(encuesta, campo), valor)
                for campo, valor in nuevos.items()
                if getattr(encuesta, campo) != valor
            }

            if not diferencias:
                continue

            con_cambios += 1
            print(f"\nEncuesta {encuesta.id} (usuario {encuesta.usuario_id}):")
            for campo, (antes, ahora) in sorted(diferencias.items()):
                print(f"    {campo}: {antes} -> {ahora}")

            if not dry_run:
                for campo, valor in nuevos.items():
                    setattr(encuesta, campo, valor)

        if dry_run:
            print(f"\n[DRY-RUN] {con_cambios} encuesta(s) cambiarían. Nada se guardó.")
        else:
            db.commit()
            print(f"\n[OK] {con_cambios} encuesta(s) actualizada(s).")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true",
        help="muestra los cambios sin escribir en la base de datos",
    )
    main(parser.parse_args().dry_run)
