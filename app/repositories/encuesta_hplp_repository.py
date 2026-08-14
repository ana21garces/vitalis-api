import uuid
from sqlalchemy.orm import Session
from app.models.encuesta_hplp import EncuestaHplp
from app.models.user import User
from app.schemas.encuesta_hplp import EncuestaCreate


def ya_respondio(db: Session, usuario_id: uuid.UUID) -> bool:
    return db.query(EncuestaHplp).filter(
        EncuestaHplp.usuario_id == usuario_id
    ).first() is not None


def crear_encuesta(
    db: Session,
    data: EncuestaCreate,
    puntajes: dict,
    usuario_id: uuid.UUID,
) -> EncuestaHplp:
    encuesta = EncuestaHplp(
        usuario_id=usuario_id,

        # RI
        ri_item_01=data.ri_item_01, ri_item_07=data.ri_item_07,
        ri_item_13=data.ri_item_13, ri_item_20=data.ri_item_20,
        ri_item_26=data.ri_item_26, ri_item_32=data.ri_item_32,
        ri_item_38=data.ri_item_38, ri_item_45=data.ri_item_45,
        ri_item_50=data.ri_item_50,
        ri_indice=puntajes["ri_indice"], ri_nivel=puntajes["ri_nivel"],

        # N
        n_item_02=data.n_item_02, n_item_08=data.n_item_08,
        n_item_14=data.n_item_14, n_item_21=data.n_item_21,
        n_item_27=data.n_item_27, n_item_33=data.n_item_33,
        n_item_39=data.n_item_39, n_item_40=data.n_item_40,
        n_item_46=data.n_item_46, n_item_51=data.n_item_51,
        n_indice=puntajes["n_indice"], n_nivel=puntajes["n_nivel"],

        # RS
        rs_item_03=data.rs_item_03, rs_item_09=data.rs_item_09,
        rs_item_15=data.rs_item_15, rs_item_22=data.rs_item_22,
        rs_item_28=data.rs_item_28, rs_item_34=data.rs_item_34,
        rs_item_41=data.rs_item_41,
        rs_indice=puntajes["rs_indice"], rs_nivel=puntajes["rs_nivel"],

        # AF
        af_item_04=data.af_item_04, af_item_10=data.af_item_10,
        af_item_16=data.af_item_16, af_item_17=data.af_item_17,
        af_item_23=data.af_item_23, af_item_29=data.af_item_29,
        af_item_35=data.af_item_35, af_item_42=data.af_item_42,
        af_item_47=data.af_item_47,
        af_indice=puntajes["af_indice"], af_nivel=puntajes["af_nivel"],

        # ME
        me_item_05=data.me_item_05, me_item_11=data.me_item_11,
        me_item_18=data.me_item_18, me_item_24=data.me_item_24,
        me_item_30=data.me_item_30, me_item_36=data.me_item_36,
        me_item_43=data.me_item_43, me_item_48=data.me_item_48,
        me_indice=puntajes["me_indice"], me_nivel=puntajes["me_nivel"],

        # PP
        pp_item_06=data.pp_item_06, pp_item_12=data.pp_item_12,
        pp_item_19=data.pp_item_19, pp_item_25=data.pp_item_25,
        pp_item_31=data.pp_item_31, pp_item_37=data.pp_item_37,
        pp_item_44=data.pp_item_44, pp_item_49=data.pp_item_49,
        pp_item_52=data.pp_item_52,
        pp_indice=puntajes["pp_indice"], pp_nivel=puntajes["pp_nivel"],

        # Global
        puntaje_crudo=puntajes["puntaje_crudo"],
        indice_global=puntajes["indice_global"],
        nivel_global=puntajes["nivel_global"],
    )

    db.add(encuesta)
    db.commit()
    db.refresh(encuesta)
    return encuesta


def obtener_por_usuario(db: Session, usuario_id: uuid.UUID):
    return (
        db.query(EncuestaHplp)
        .filter(EncuestaHplp.usuario_id == usuario_id)
        .order_by(EncuestaHplp.fecha_respuesta.desc())
        .all()
    )


def obtener_ultimo(db: Session, usuario_id: uuid.UUID) -> EncuestaHplp | None:
    return (
        db.query(EncuestaHplp)
        .filter(EncuestaHplp.usuario_id == usuario_id)
        .order_by(EncuestaHplp.fecha_respuesta.desc())
        .first()
    )


def eliminar(db: Session, encuesta_id: int) -> bool:
    encuesta = db.query(EncuestaHplp).filter(EncuestaHplp.id == encuesta_id).first()
    if not encuesta:
        return False
    db.delete(encuesta)
    db.commit()
    return True


def _base_resultados_query(db: Session, facultad: str | None, carrera: str | None, tipo_usuario: str | None):
    """Subconsulta base: encuesta más reciente por usuario con filtros opcionales."""
    from sqlalchemy import func

    subq = (
        db.query(
            EncuestaHplp.usuario_id,
            func.max(EncuestaHplp.id).label("ultimo_id"),
        )
        .group_by(EncuestaHplp.usuario_id)
        .subquery()
    )

    q = (
        db.query(EncuestaHplp, User)
        .join(subq, EncuestaHplp.id == subq.c.ultimo_id)
        .join(User, User.id == EncuestaHplp.usuario_id)
    )

    if facultad:
        q = q.filter(User.facultad.ilike(facultad))
    if carrera:
        q = q.filter(User.program.ilike(carrera))
    if tipo_usuario:
        q = q.filter(User.tipo_usuario.ilike(tipo_usuario))

    return q.order_by(User.facultad, User.program, User.full_name).all()


def obtener_opciones_filtros(db: Session) -> dict:
    """Devuelve los valores únicos disponibles para poblar los filtros del frontend."""
    from sqlalchemy import func, distinct

    subq = (
        db.query(func.max(EncuestaHplp.id).label("ultimo_id"))
        .group_by(EncuestaHplp.usuario_id)
        .subquery()
    )

    base = (
        db.query(User)
        .join(EncuestaHplp, User.id == EncuestaHplp.usuario_id)
        .join(subq, EncuestaHplp.id == subq.c.ultimo_id)
    )

    facultades = [
        r[0] for r in base.with_entities(distinct(User.facultad))
        .filter(User.facultad.isnot(None))
        .order_by(User.facultad)
        .all()
    ]
    carreras = [
        r[0] for r in base.with_entities(distinct(User.program))
        .filter(User.program.isnot(None))
        .order_by(User.program)
        .all()
    ]
    tipos = [
        r[0] for r in base.with_entities(distinct(User.tipo_usuario))
        .filter(User.tipo_usuario.isnot(None))
        .order_by(User.tipo_usuario)
        .all()
    ]

    return {"facultades": facultades, "carreras": carreras, "tipos_usuario": tipos}


def obtener_resumen_admin(db: Session) -> dict:
    """Cuenta totales para el Resumen General del administrador."""
    from sqlalchemy import func
    from app.models.user import UserRole

    roles_profesionales = [
        UserRole.ADMIN.value,
        UserRole.CAPELLAN.value,
        UserRole.ACTIVIDAD_FISICA.value,
        UserRole.RESPONSABILIDAD_SALUD.value,
        UserRole.HEALTH_MANAGER.value,
    ]

    total_usuarios = db.query(User).filter(User.role.notin_(roles_profesionales)).count()
    completaron = (
        db.query(func.count(func.distinct(EncuestaHplp.usuario_id)))
        .join(User, User.id == EncuestaHplp.usuario_id)
        .filter(User.role.notin_(roles_profesionales))
        .scalar()
    )
    sin_completar = total_usuarios - completaron
    tasa = round((completaron / total_usuarios * 100), 1) if total_usuarios > 0 else 0.0

    return {
        "total_usuarios": total_usuarios,
        "completaron_encuesta": completaron,
        "sin_completar": sin_completar,
        "tasa_participacion": tasa,
    }


def obtener_resultados_rs_todos(
    db: Session,
    facultad: str | None = None,
    carrera: str | None = None,
    tipo_usuario: str | None = None,
) -> list[tuple[EncuestaHplp, User]]:
    return _base_resultados_query(db, facultad, carrera, tipo_usuario)


def obtener_resultados_af_todos(
    db: Session,
    facultad: str | None = None,
    carrera: str | None = None,
    tipo_usuario: str | None = None,
) -> list[tuple[EncuestaHplp, User]]:
    return _base_resultados_query(db, facultad, carrera, tipo_usuario)


def obtener_resultados_pp_todos(
    db: Session,
    facultad: str | None = None,
    carrera: str | None = None,
    tipo_usuario: str | None = None,
) -> list[tuple[EncuestaHplp, User]]:
    return _base_resultados_query(db, facultad, carrera, tipo_usuario)
