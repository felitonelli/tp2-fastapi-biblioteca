"""Datos de ejemplo para probar la API desde Swagger.
Solo se cargan si la base está vacía."""

from sqlmodel import Session, select

from models import Autor, Libro, Socio


def cargar_datos_iniciales(session: Session) -> None:
    if session.exec(select(Libro)).first():
        return

    borges = Autor(nombre="Jorge Luis Borges", nacionalidad="Argentina")
    bioy = Autor(nombre="Adolfo Bioy Casares", nacionalidad="Argentina")
    cortazar = Autor(nombre="Julio Cortázar", nacionalidad="Argentina")

    session.add_all([
        Libro(titulo="Ficciones", isbn="978-950-04-0001-1", stock=3, anio=1944, autores=[borges]),
        Libro(titulo="Seis problemas para don Isidro Parodi", isbn="978-950-04-0002-8",
              stock=1, anio=1942, autores=[borges, bioy]),
        Libro(titulo="Rayuela", isbn="978-950-04-0003-5", stock=0, anio=1963, autores=[cortazar]),
        Socio(nombre="Lucía Fernández", email="lucia@email.com"),
        Socio(nombre="Martín Rossi", email="martin@email.com", activo=False),
    ])
    session.commit()
