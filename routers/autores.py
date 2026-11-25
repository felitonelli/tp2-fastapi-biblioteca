from collections.abc import Sequence

from fastapi import APIRouter, status

from database import SessionDep
from models import Autor, AutorCreate, AutorRead, AutorUpdate
from services import autores

router = APIRouter(prefix="/autores", tags=["Autores"])


@router.post("", response_model=AutorRead, status_code=status.HTTP_201_CREATED)
def crear_autor(datos: AutorCreate, session: SessionDep) -> Autor:
    return autores.crear(session, datos)


@router.get("", response_model=list[AutorRead])
def listar_autores(session: SessionDep) -> Sequence[Autor]:
    return autores.listar(session)


@router.get("/{autor_id}", response_model=AutorRead)
def obtener_autor(autor_id: int, session: SessionDep) -> Autor:
    return autores.obtener(session, autor_id)


@router.patch("/{autor_id}", response_model=AutorRead)
def modificar_autor(autor_id: int, datos: AutorUpdate, session: SessionDep) -> Autor:
    return autores.modificar(session, autor_id, datos)


@router.delete("/{autor_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_autor(autor_id: int, session: SessionDep) -> None:
    autores.eliminar(session, autor_id)
