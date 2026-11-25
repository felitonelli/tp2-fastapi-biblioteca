"""Tests directos de la capa services (sin HTTP)."""
from datetime import date

import pytest
from sqlmodel import select

from models import Libro, Socio
from services import prestamos
from services.seed import cargar_datos_iniciales


@pytest.mark.parametrize(
    "devolucion, multa_esperada",
    [
        (date(2026, 11, 10), 0),     # antes del vencimiento
        (date(2026, 11, 15), 0),     # el mismo día que vence
        (date(2026, 11, 16), 100),   # 1 día tarde
        (date(2026, 12, 15), 3000),  # 30 días tarde
    ],
)
def test_calcular_multa(devolucion, multa_esperada):
    assert prestamos.calcular_multa(date(2026, 11, 15), devolucion) == multa_esperada


def test_calcular_vencimiento():
    assert prestamos.calcular_vencimiento(date(2026, 2, 20)) == date(2026, 3, 6)


def test_seed_carga_datos_una_sola_vez(session):
    cargar_datos_iniciales(session)
    cargar_datos_iniciales(session)  # la segunda vez no duplica
    libros = session.exec(select(Libro)).all()
    assert len(libros) == 3
    assert len(session.exec(select(Socio)).all()) == 2
    parodi = next(lib for lib in libros if lib.isbn == "978-950-04-0002-8")
    assert len(parodi.autores) == 2


def test_inicio(client):
    assert client.get("/").status_code == 200
