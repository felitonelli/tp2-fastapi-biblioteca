from collections.abc import Sequence

from fastapi import APIRouter, status

from database import SessionDep
from models import Prestamo, PrestamoRead, Socio, SocioCreate, SocioRead, SocioUpdate
from services import prestamos, socios

router = APIRouter(prefix="/socios", tags=["Socios"])


@router.post("", response_model=SocioRead, status_code=status.HTTP_201_CREATED)
def crear_socio(datos: SocioCreate, session: SessionDep) -> Socio:
    return socios.crear(session, datos)


@router.get("", response_model=list[SocioRead])
def listar_socios(session: SessionDep) -> Sequence[Socio]:
    return socios.listar(session)


@router.get("/{socio_id}", response_model=SocioRead)
def obtener_socio(socio_id: int, session: SessionDep) -> Socio:
    return socios.obtener(session, socio_id)


@router.patch("/{socio_id}", response_model=SocioRead)
def modificar_socio(socio_id: int, datos: SocioUpdate, session: SessionDep) -> Socio:
    return socios.modificar(session, socio_id, datos)


@router.delete("/{socio_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_socio(socio_id: int, session: SessionDep) -> None:
    socios.eliminar(session, socio_id)


@router.get("/{socio_id}/prestamos", response_model=list[PrestamoRead])
def prestamos_del_socio(socio_id: int, session: SessionDep, activos: bool | None = None) -> Sequence[Prestamo]:
    """- `activos=true`: solo los que no fueron devueltos
    - `activos=false`: solo los devueltos
    - sin filtro: todos"""
    return prestamos.prestamos_de_socio(session, socio_id, activos)
