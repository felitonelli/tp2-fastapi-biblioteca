from collections.abc import Sequence

from fastapi import APIRouter, status

from database import SessionDep
from models import Libro, LibroConAutores, LibroCreate, LibroUpdate
from services import libros

router = APIRouter(prefix="/libros", tags=["Libros"])


@router.post("", response_model=LibroConAutores, status_code=status.HTTP_201_CREATED)
def crear_libro(datos: LibroCreate, session: SessionDep) -> Libro:
    return libros.crear(session, datos)


@router.get("", response_model=list[LibroConAutores])
def listar_libros(session: SessionDep, disponibles: bool | None = None) -> Sequence[Libro]:
    """- sin filtro: todos
    - `disponibles=true`: libros con stock > 0
    - `disponibles=false`: libros sin stock"""
    return libros.listar(session, disponibles)


@router.get("/{libro_id}", response_model=LibroConAutores)
def obtener_libro(libro_id: int, session: SessionDep) -> Libro:
    return libros.obtener(session, libro_id)


@router.patch("/{libro_id}", response_model=LibroConAutores)
def modificar_libro(libro_id: int, datos: LibroUpdate, session: SessionDep) -> Libro:
    return libros.modificar(session, libro_id, datos)


@router.delete("/{libro_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_libro(libro_id: int, session: SessionDep) -> None:
    libros.eliminar(session, libro_id)


@router.post("/{libro_id}/autores/{autor_id}", response_model=LibroConAutores, status_code=status.HTTP_201_CREATED)
def asociar_autor(libro_id: int, autor_id: int, session: SessionDep) -> Libro:
    return libros.asociar_autor(session, libro_id, autor_id)


@router.delete("/{libro_id}/autores/{autor_id}", response_model=LibroConAutores)
def desasociar_autor(libro_id: int, autor_id: int, session: SessionDep) -> Libro:
    return libros.desasociar_autor(session, libro_id, autor_id)
