from collections.abc import Sequence

from sqlmodel import Session, select

from models import Socio, SocioCreate, SocioUpdate
from services.errors import ConflictError, NotFoundError


def listar(session: Session) -> Sequence[Socio]:
    return session.exec(select(Socio)).all()


def obtener(session: Session, socio_id: int) -> Socio:
    socio = session.get(Socio, socio_id)
    if not socio:
        raise NotFoundError(f"Socio {socio_id} no encontrado")
    return socio


def _validar_email_unico(session: Session, email: str, excepto_id: int | None = None) -> None:
    existente = session.exec(select(Socio).where(Socio.email == email)).first()
    if existente and existente.id != excepto_id:
        raise ConflictError(f"Ya existe un socio con el email {email}")


def crear(session: Session, datos: SocioCreate) -> Socio:
    datos.email = datos.email.lower()
    _validar_email_unico(session, datos.email)
    socio = Socio.model_validate(datos)
    session.add(socio)
    session.commit()
    session.refresh(socio)
    return socio


def modificar(session: Session, socio_id: int, datos: SocioUpdate) -> Socio:
    socio = obtener(session, socio_id)
    if datos.email is not None:
        datos.email = datos.email.lower()
        _validar_email_unico(session, datos.email, excepto_id=socio_id)
    socio.sqlmodel_update(datos.model_dump(exclude_unset=True))
    session.add(socio)
    session.commit()
    session.refresh(socio)
    return socio


def eliminar(session: Session, socio_id: int) -> None:
    socio = obtener(session, socio_id)
    if socio.prestamos:
        raise ConflictError("No se puede borrar un socio con préstamos registrados; se puede marcar como inactivo")
    session.delete(socio)
    session.commit()
