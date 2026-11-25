from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint
from sqlmodel import Field, Relationship, SQLModel

from models.autor import AutorRead
from models.libro_autor import LibroAutor

if TYPE_CHECKING:
    from models.autor import Autor
    from models.prestamo import Prestamo


class LibroBase(SQLModel):
    titulo: str = Field(min_length=1)
    isbn: str = Field(unique=True, index=True, min_length=1)
    stock: int = Field(default=0, ge=0)
    anio: int


class Libro(LibroBase, table=True):
    # La base de datos también rechaza un stock negativo
    __table_args__ = (CheckConstraint("stock >= 0", name="stock_no_negativo"),)

    id: int | None = Field(default=None, primary_key=True)
    autores: list["Autor"] = Relationship(back_populates="libros", link_model=LibroAutor)
    prestamos: list["Prestamo"] = Relationship(back_populates="libro")


class LibroCreate(LibroBase):
    pass


class LibroUpdate(SQLModel):
    titulo: str | None = Field(default=None, min_length=1)
    isbn: str | None = Field(default=None, min_length=1)
    stock: int | None = Field(default=None, ge=0)
    anio: int | None = None


class LibroRead(LibroBase):
    id: int


class LibroConAutores(LibroRead):
    autores: list[AutorRead] = []
