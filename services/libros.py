from collections.abc import Sequence

from sqlmodel import Session, col, select

from models import Libro, LibroCreate, LibroUpdate
from services import autores
from services.errors import ConflictError, NotFoundError


def listar(session: Session, disponibles: bool | None = None) -> Sequence[Libro]:
    consulta = select(Libro)
    if disponibles is True:
        consulta = consulta.where(col(Libro.stock) > 0)
    elif disponibles is False:
        consulta = consulta.where(col(Libro.stock) == 0)
    return session.exec(consulta).all()


def obtener(session: Session, libro_id: int) -> Libro:
    libro = session.get(Libro, libro_id)
    if not libro:
        raise NotFoundError(f"Libro {libro_id} no encontrado")
    return libro


def _validar_isbn_unico(session: Session, isbn: str, excepto_id: int | None = None) -> None:
    existente = session.exec(select(Libro).where(Libro.isbn == isbn)).first()
    if existente and existente.id != excepto_id:
        raise ConflictError(f"Ya existe un libro con ISBN {isbn}")


def crear(session: Session, datos: LibroCreate) -> Libro:
    _validar_isbn_unico(session, datos.isbn)
    libro = Libro.model_validate(datos)
    session.add(libro)
    session.commit()
    session.refresh(libro)
    return libro


def modificar(session: Session, libro_id: int, datos: LibroUpdate) -> Libro:
    libro = obtener(session, libro_id)
    if datos.isbn is not None:
        _validar_isbn_unico(session, datos.isbn, excepto_id=libro_id)
    libro.sqlmodel_update(datos.model_dump(exclude_unset=True))
    session.add(libro)
    session.commit()
    session.refresh(libro)
    return libro


def eliminar(session: Session, libro_id: int) -> None:
    libro = obtener(session, libro_id)
    if libro.prestamos:
        raise ConflictError("No se puede borrar un libro con préstamos registrados")
    session.delete(libro)
    session.commit()


def asociar_autor(session: Session, libro_id: int, autor_id: int) -> Libro:
    libro = obtener(session, libro_id)
    autor = autores.obtener(session, autor_id)
    if autor in libro.autores:
        raise ConflictError("El autor ya está asociado a ese libro")
    libro.autores.append(autor)
    session.add(libro)
    session.commit()
    session.refresh(libro)
    return libro


def desasociar_autor(session: Session, libro_id: int, autor_id: int) -> Libro:
    libro = obtener(session, libro_id)
    autor = autores.obtener(session, autor_id)
    if autor not in libro.autores:
        raise NotFoundError("El autor no está asociado a ese libro")
    libro.autores.remove(autor)
    session.add(libro)
    session.commit()
    session.refresh(libro)
    return libro
