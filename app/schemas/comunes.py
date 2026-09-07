from typing import Annotated

from pydantic import EmailStr
from pydantic.functional_validators import AfterValidator


def _normalizar_correo(valor: str) -> str:
    return valor.strip().lower()


CorreoNormalizado = Annotated[EmailStr, AfterValidator(_normalizar_correo)]
