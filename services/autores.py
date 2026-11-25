from collections.abc import Sequence

from sqlmodel import Session, select

from models import Autor, AutorCreate, AutorUpdate
from services.errors import NotFoundError


def listar(session: Session) -> Sequence[Autor]:
    return session.exec(select(Autor)).all()


def obtener(session: Session, autor_id: int) -> Autor:
    autor = session.get(Autor, autor_id)
    if not autor:
        raise NotFoundError(f"Autor {autor_id} no encontrado")
    return autor


def crear(session: Session, datos: AutorCreate) -> Autor:
    autor = Autor.model_validate(datos)
    session.add(autor)
    session.commit()
    session.refresh(autor)
    return autor


def modificar(session: Session, autor_id: int, datos: AutorUpdate) -> Autor:
    autor = obtener(session, autor_id)
    autor.sqlmodel_update(datos.model_dump(exclude_unset=True))
    session.add(autor)
    session.commit()
    session.refresh(autor)
    return autor


def eliminar(session: Session, autor_id: int) -> None:
    # Al borrarlo, SQLAlchemy también borra sus filas en LibroAutor
    autor = obtener(session, autor_id)
    session.delete(autor)
    session.commit()
