"""Reglas de negocio de los préstamos.

1. Un socio no puede tener más de 3 préstamos activos       → 409
2. No se presta un libro sin stock; al prestar se descuenta 1 → 409
3. Un socio inactivo no puede pedir préstamos               → 403
4. fecha_vencimiento = fecha_prestamo + 14 días
5. Al devolver se repone el stock y se calcula la multa ($100 × día de atraso)
6. No se puede devolver un préstamo ya devuelto             → 409
7. Recurso inexistente                                       → 404
"""

from collections.abc import Sequence
from datetime import date, timedelta

from sqlmodel import Session, col, select

from models import DevolucionRequest, Prestamo, PrestamoCreate
from services import libros, socios
from services.errors import ConflictError, ForbiddenError, InvalidDataError, NotFoundError

MAX_PRESTAMOS_ACTIVOS = 3
DIAS_DE_PLAZO = 14
MULTA_POR_DIA = 100


def calcular_vencimiento(fecha_prestamo: date) -> date:
    return fecha_prestamo + timedelta(days=DIAS_DE_PLAZO)


def calcular_multa(fecha_vencimiento: date, fecha_devolucion: date) -> int:
    dias_atraso = (fecha_devolucion - fecha_vencimiento).days
    return max(dias_atraso, 0) * MULTA_POR_DIA


def contar_activos(session: Session, socio_id: int) -> int:
    consulta = select(Prestamo).where(
        Prestamo.socio_id == socio_id,
        col(Prestamo.fecha_devolucion).is_(None),
    )
    return len(session.exec(consulta).all())


def listar(session: Session, activos: bool | None = None, socio_id: int | None = None) -> Sequence[Prestamo]:
    consulta = select(Prestamo)
    if socio_id is not None:
        consulta = consulta.where(Prestamo.socio_id == socio_id)
    if activos is True:
        consulta = consulta.where(col(Prestamo.fecha_devolucion).is_(None))
    elif activos is False:
        consulta = consulta.where(col(Prestamo.fecha_devolucion).is_not(None))
    return session.exec(consulta).all()


def obtener(session: Session, prestamo_id: int) -> Prestamo:
    prestamo = session.get(Prestamo, prestamo_id)
    if not prestamo:
        raise NotFoundError(f"Préstamo {prestamo_id} no encontrado")
    return prestamo


def prestamos_de_socio(session: Session, socio_id: int, activos: bool | None = None) -> Sequence[Prestamo]:
    socios.obtener(session, socio_id)  # regla 7: 404 si el socio no existe
    return listar(session, activos=activos, socio_id=socio_id)


def registrar_prestamo(session: Session, datos: PrestamoCreate) -> Prestamo:
    socio = socios.obtener(session, datos.socio_id)  # regla 7
    libro = libros.obtener(session, datos.libro_id)  # regla 7

    if not socio.activo:  # regla 3
        raise ForbiddenError("El socio está inactivo y no puede pedir préstamos")

    if contar_activos(session, datos.socio_id) >= MAX_PRESTAMOS_ACTIVOS:  # regla 1
        raise ConflictError(f"El socio ya tiene {MAX_PRESTAMOS_ACTIVOS} préstamos activos")

    if libro.stock <= 0:  # regla 2
        raise ConflictError("El libro no tiene stock disponible")

    fecha_prestamo = datos.fecha_prestamo or date.today()
    prestamo = Prestamo(
        socio_id=datos.socio_id,
        libro_id=datos.libro_id,
        fecha_prestamo=fecha_prestamo,
        fecha_vencimiento=calcular_vencimiento(fecha_prestamo),  # regla 4
    )
    libro.stock -= 1  # regla 2

    session.add(prestamo)
    session.add(libro)
    session.commit()
    session.refresh(prestamo)
    return prestamo


def registrar_devolucion(session: Session, prestamo_id: int, datos: DevolucionRequest) -> Prestamo:
    prestamo = obtener(session, prestamo_id)  # regla 7

    if prestamo.fecha_devolucion is not None:  # regla 6
        raise ConflictError("El préstamo ya fue devuelto")

    fecha_devolucion = datos.fecha_devolucion or date.today()
    if fecha_devolucion < prestamo.fecha_prestamo:
        raise InvalidDataError("La fecha de devolución no puede ser anterior a la del préstamo")

    prestamo.fecha_devolucion = fecha_devolucion
    prestamo.multa = calcular_multa(prestamo.fecha_vencimiento, fecha_devolucion)  # regla 5
    prestamo.libro.stock += 1  # regla 5: se repone el stock

    session.add(prestamo)
    session.commit()
    session.refresh(prestamo)
    return prestamo
