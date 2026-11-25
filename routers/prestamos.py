from collections.abc import Sequence

from fastapi import APIRouter, status

from database import SessionDep
from models import DevolucionRequest, Prestamo, PrestamoCreate, PrestamoRead
from services import prestamos

router = APIRouter(prefix="/prestamos", tags=["Préstamos"])


@router.post("", response_model=PrestamoRead, status_code=status.HTTP_201_CREATED)
def registrar_prestamo(datos: PrestamoCreate, session: SessionDep) -> Prestamo:
    """`fecha_prestamo` es opcional (por defecto, hoy). Vence a los 14 días."""
    return prestamos.registrar_prestamo(session, datos)


@router.get("", response_model=list[PrestamoRead])
def listar_prestamos(session: SessionDep, activos: bool | None = None) -> Sequence[Prestamo]:
    return prestamos.listar(session, activos=activos)


@router.get("/{prestamo_id}", response_model=PrestamoRead)
def obtener_prestamo(prestamo_id: int, session: SessionDep) -> Prestamo:
    return prestamos.obtener(session, prestamo_id)


@router.post("/{prestamo_id}/devolucion", response_model=PrestamoRead)
def registrar_devolucion(
    prestamo_id: int, session: SessionDep, datos: DevolucionRequest | None = None
) -> Prestamo:
    """El body es opcional: `fecha_devolucion` por defecto es hoy.
    Multa: $100 por cada día de atraso."""
    return prestamos.registrar_devolucion(session, prestamo_id, datos or DevolucionRequest())
