from sqlmodel import Field, SQLModel


class LibroAutor(SQLModel, table=True):
    """Tabla intermedia de la relación N-N entre Libro y Autor."""

    libro_id: int | None = Field(default=None, foreign_key="libro.id", primary_key=True)
    autor_id: int | None = Field(default=None, foreign_key="autor.id", primary_key=True)
