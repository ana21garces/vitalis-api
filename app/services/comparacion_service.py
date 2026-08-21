"""
Comparación entre dos mediciones: qué cambió del diagnóstico al seguimiento.

Se compara **por pares**: solo entran las personas que respondieron las DOS
mediciones. Promediar todos los de una ronda contra todos los de la otra mezcla
poblaciones distintas (quien no volvió a responder) y el cambio que se ve puede
ser puro efecto de quién contestó, no de la intervención.

El nivel y el índice no se recalculan: se leen de las columnas que ya guardó la
encuesta, las mismas que ve la persona en su panel.
"""
from sqlalchemy.orm import Session

from app.models.ciclo_medicion import CicloMedicion
from app.models.encuesta_hplp import EncuestaHplp
from app.models.user import User
from app.services.reportes_service import DIMENSIONES, ROLES_PROFESIONALES

# Orden de los niveles, para saber si alguien subió o bajó.
ORDEN_NIVEL = {"pobre": 0, "moderado": 1, "bueno": 2, "excelente": 3}

# El índice global no está en DIMENSIONES: se agrega aparte porque es el
# resumen que encabeza la comparación.
AMBITOS = [("indice_global", "Índice global", "nivel_global")] + [
    (f"{prefijo}_indice", etiqueta, f"{prefijo}_nivel") for prefijo, etiqueta in DIMENSIONES
]


def _respuestas_por_usuario(db: Session, ciclo_id: int) -> dict:
    """Encuesta de cada usuario en esa medición, sin cuentas profesionales."""
    filas = (
        db.query(EncuestaHplp, User)
        .join(User, User.id == EncuestaHplp.usuario_id)
        .filter(EncuestaHplp.ciclo_id == ciclo_id)
        .filter(User.role.notin_(ROLES_PROFESIONALES))
        .all()
    )
    return {usuario.id: (encuesta, usuario) for encuesta, usuario in filas}


def _promedio(valores: list[float]) -> float:
    return round(sum(valores) / len(valores), 1) if valores else 0.0


def _cambio_de_nivel(nivel_base: str | None, nivel_actual: str | None) -> int:
    """1 si subió de nivel, -1 si bajó, 0 si se mantuvo o falta el dato."""
    a = ORDEN_NIVEL.get((nivel_base or "").lower())
    b = ORDEN_NIVEL.get((nivel_actual or "").lower())
    if a is None or b is None:
        return 0
    return (b > a) - (b < a)


def comparar(db: Session, base: CicloMedicion, seguimiento: CicloMedicion) -> dict:
    respuestas_base = _respuestas_por_usuario(db, base.id)
    respuestas_seg = _respuestas_por_usuario(db, seguimiento.id)
    comunes = sorted(
        set(respuestas_base) & set(respuestas_seg),
        key=lambda uid: respuestas_base[uid][1].full_name,
    )

    dimensiones = []
    for campo_indice, etiqueta, campo_nivel in AMBITOS:
        indices_base, indices_seg = [], []
        mejoraron = empeoraron = se_mantuvieron = 0
        for uid in comunes:
            enc_base = respuestas_base[uid][0]
            enc_seg = respuestas_seg[uid][0]
            valor_base = getattr(enc_base, campo_indice)
            valor_seg = getattr(enc_seg, campo_indice)
            if valor_base is None or valor_seg is None:
                continue
            indices_base.append(valor_base)
            indices_seg.append(valor_seg)
            cambio = _cambio_de_nivel(
                getattr(enc_base, campo_nivel), getattr(enc_seg, campo_nivel)
            )
            if cambio > 0:
                mejoraron += 1
            elif cambio < 0:
                empeoraron += 1
            else:
                se_mantuvieron += 1

        promedio_base = _promedio(indices_base)
        promedio_seg = _promedio(indices_seg)
        dimensiones.append({
            "clave": campo_indice.replace("_indice", ""),
            "etiqueta": etiqueta,
            "promedio_base": promedio_base,
            "promedio_seguimiento": promedio_seg,
            "delta": round(promedio_seg - promedio_base, 1),
            "mejoraron": mejoraron,
            "se_mantuvieron": se_mantuvieron,
            "empeoraron": empeoraron,
        })

    # Por facultad, solo con el índice global: es el corte que sirve para saber
    # dónde poner el esfuerzo, y con seis dimensiones por facultad la tabla se
    # vuelve ilegible.
    por_facultad: dict[str, dict] = {}
    for uid in comunes:
        enc_base, usuario = respuestas_base[uid]
        enc_seg = respuestas_seg[uid][0]
        if enc_base.indice_global is None or enc_seg.indice_global is None:
            continue
        grupo = por_facultad.setdefault(
            usuario.facultad or "Sin facultad", {"base": [], "seguimiento": []}
        )
        grupo["base"].append(enc_base.indice_global)
        grupo["seguimiento"].append(enc_seg.indice_global)

    facultades = []
    for nombre, grupo in por_facultad.items():
        promedio_base = _promedio(grupo["base"])
        promedio_seg = _promedio(grupo["seguimiento"])
        facultades.append({
            "facultad": nombre,
            "total": len(grupo["base"]),
            "promedio_base": promedio_base,
            "promedio_seguimiento": promedio_seg,
            "delta": round(promedio_seg - promedio_base, 1),
        })
    # Peor cambio primero: la facultad que necesita más atención.
    facultades.sort(key=lambda f: f["delta"])

    return {
        "base": {"id": base.id, "numero": base.numero, "nombre": base.nombre},
        "seguimiento": {
            "id": seguimiento.id,
            "numero": seguimiento.numero,
            "nombre": seguimiento.nombre,
        },
        "usuarios_comparados": len(comunes),
        "respondieron_base": len(respuestas_base),
        "respondieron_seguimiento": len(respuestas_seg),
        "dimensiones": dimensiones,
        "facultades": facultades,
    }
