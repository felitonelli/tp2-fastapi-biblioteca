from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlmodel import Session

from database import create_db_and_tables, engine
from routers import autores, libros, prestamos, socios
from services.errors import ConflictError, ForbiddenError, InvalidDataError, NotFoundError
from services.seed import cargar_datos_iniciales


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        cargar_datos_iniciales(session)
    yield


app = FastAPI(title="Sistema de Biblioteca", lifespan=lifespan)

app.include_router(autores.router)
app.include_router(libros.router)
app.include_router(socios.router)
app.include_router(prestamos.router)


# Cada error de negocio de los services se traduce a su código HTTP
ERRORES_HTTP: dict[type[Exception], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    ForbiddenError: status.HTTP_403_FORBIDDEN,
    InvalidDataError: status.HTTP_422_UNPROCESSABLE_CONTENT,
}


async def error_de_negocio(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=ERRORES_HTTP[type(exc)], content={"detail": str(exc)})


for tipo_error in ERRORES_HTTP:
    app.add_exception_handler(tipo_error, error_de_negocio)


@app.get("/", tags=["Inicio"])
def inicio():
    return {"message": "Sistema de Biblioteca. Documentación en /docs"}
