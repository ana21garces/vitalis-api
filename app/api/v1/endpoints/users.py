import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user, requiere_admin
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.encuesta_hplp import EncuestaHplp
from app.models.notificacion import Notificacion
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    UserResponse,
    CambiarRolRequest,
    CambiarEstadoRequest,
    CrearUsuarioRequest,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def leer_perfil_propio(current_user: User = Depends(get_current_user)):
    """Devuelve el perfil del usuario autenticado.

    Es la única forma que tiene el cliente de saber quién ha iniciado sesión:
    el JWT solo lleva el id, el correo y el rol. Sin esto, las pantallas
    mostraban nombres fijos como «Estudiante» o «Prof. Actividad Física».
    """
    return current_user


@router.get("", response_model=List[UserResponse])
def listar_usuarios(
    _admin: User = Depends(requiere_admin),
    db: Session = Depends(get_db),
):
    """Lista todos los usuarios. Solo el administrador (gestión de usuarios)."""
    return UserRepository(db).listar()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    data: CrearUsuarioRequest,
    _admin: User = Depends(requiere_admin),
    db: Session = Depends(get_db),
):
    """Crea un usuario con el rol indicado. Solo el administrador.

    Pensado para dar de alta cuentas profesionales (o cualquier rol) sin pasar
    por el registro público. La cuenta nace activa y verificada.
    """
    repo = UserRepository(db)
    if repo.get_by_email(data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo ya está registrado",
        )
    nuevo = User(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=data.role.value,
        is_active=True,
        is_verified=True,
    )
    return repo.create(nuevo)


@router.patch("/{user_id}/role", response_model=UserResponse)
def cambiar_rol(
    user_id: uuid.UUID,
    data: CambiarRolRequest,
    admin: User = Depends(requiere_admin),
    db: Session = Depends(get_db),
):
    """Asigna un rol nuevo a un usuario. Solo el administrador.

    El administrador no puede cambiarse el rol a sí mismo, para no perder por
    error su propio acceso y dejar la plataforma sin administrador.
    """
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes cambiar tu propio rol",
        )
    if (
        user.role == UserRole.ADMIN.value
        and data.role != UserRole.ADMIN
        and repo.contar_admins() <= 1
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe quedar al menos un administrador",
        )
    user.role = data.role.value
    return repo.update(user)


@router.patch("/{user_id}/estado", response_model=UserResponse)
def cambiar_estado(
    user_id: uuid.UUID,
    data: CambiarEstadoRequest,
    admin: User = Depends(requiere_admin),
    db: Session = Depends(get_db),
):
    """Activa o desactiva una cuenta. Solo el administrador.

    El administrador no puede desactivarse a sí mismo.
    """
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes cambiar tu propio estado",
        )
    if (
        user.role == UserRole.ADMIN.value
        and not data.is_active
        and repo.contar_admins() <= 1
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes suspender al último administrador",
        )
    user.is_active = data.is_active
    return repo.update(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_usuario(
    user_id: uuid.UUID,
    admin: User = Depends(requiere_admin),
    db: Session = Depends(get_db),
):
    """Elimina un usuario de forma permanente. Solo el administrador.

    Antes de borrar la cuenta se limpian sus datos relacionados (encuestas y
    notificaciones) para no dejar registros huérfanos ni romper las llaves
    foráneas. El administrador no puede eliminarse a sí mismo.
    """
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar tu propia cuenta",
        )
    if user.role == UserRole.ADMIN.value and repo.contar_admins() <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar al último administrador",
        )
    db.query(EncuestaHplp).filter(EncuestaHplp.usuario_id == user.id).delete(
        synchronize_session=False
    )
    db.query(Notificacion).filter(
        or_(
            Notificacion.remitente_id == user.id,
            Notificacion.destinatario_id == user.id,
        )
    ).delete(synchronize_session=False)
    db.delete(user)
    db.commit()
    return None
