# Se importan todos los modelos para que SQLModel conozca todas las tablas
# y pueda resolver las relaciones entre ellas.
from models.libro_autor import LibroAutor
from models.autor import Autor, AutorCreate, AutorRead, AutorUpdate
from models.libro import Libro, LibroConAutores, LibroCreate, LibroRead, LibroUpdate
from models.socio import Socio, SocioCreate, SocioRead, SocioUpdate
from models.prestamo import DevolucionRequest, Prestamo, PrestamoCreate, PrestamoRead

__all__ = [
    "LibroAutor",
    "Autor", "AutorCreate", "AutorRead", "AutorUpdate",
    "Libro", "LibroConAutores", "LibroCreate", "LibroRead", "LibroUpdate",
    "Socio", "SocioCreate", "SocioRead", "SocioUpdate",
    "DevolucionRequest", "Prestamo", "PrestamoCreate", "PrestamoRead",
]
