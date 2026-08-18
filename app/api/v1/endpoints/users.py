from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def leer_perfil_propio(current_user: User = Depends(get_current_user)):
    """Devuelve el perfil del usuario autenticado.

    Es la única forma que tiene el cliente de saber quién ha iniciado sesión:
    el JWT solo lleva el id, el correo y el rol. Sin esto, las pantallas
    mostraban nombres fijos como «Estudiante» o «Prof. Actividad Física».

    Un usuario solo puede leer su propio perfil; para ver el de otro haría
    falta la gestión de usuarios del administrador, que aún no existe.
    """
    return current_user
