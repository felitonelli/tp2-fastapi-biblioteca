# TP: Sistema de Biblioteca (FastAPI + SQLModel)

API REST para gestionar el catálogo de una biblioteca (autores, libros, socios) y sus préstamos, con las reglas de negocio de la consigna y sus códigos HTTP.

## Estructura

```
main.py            crea la app, registra routers y traduce errores de negocio a HTTP
database.py        engine de SQLite y sesión (dependencia SessionDep)
models/            tablas SQLModel + esquemas de entrada/salida
  autor.py           Autor
  libro.py           Libro (+ LibroConAutores para las respuestas)
  libro_autor.py     LibroAutor: tabla intermedia N-N
  socio.py           Socio
  prestamo.py        Prestamo
routers/           solo HTTP: reciben el pedido y llaman al service
  autores.py  libros.py  socios.py  prestamos.py
services/          lógica y reglas de negocio (no saben nada de HTTP)
  autores.py  libros.py  socios.py
  prestamos.py       reglas 1 a 7
  errors.py          NotFoundError, ConflictError, ForbiddenError, InvalidDataError
  seed.py            datos de ejemplo
tests/             pytest con base de datos en memoria
```

Los services lanzan errores propios (`NotFoundError`, `ConflictError`, etc.) y `main.py` los convierte en 404, 409, 403 o 422. Así los routers no tienen reglas de negocio y los services no dependen de FastAPI.

## Modelo de datos

| Entidad | Campos |
|---|---|
| `Autor` | id, nombre, nacionalidad |
| `Libro` | id, titulo, isbn (único), stock (≥ 0), anio |
| `LibroAutor` | libro_id, autor_id (tabla intermedia) |
| `Socio` | id, nombre, email (único, validado), activo |
| `Prestamo` | id, socio_id, libro_id, fecha_prestamo, fecha_vencimiento, fecha_devolucion (nullable), multa |

Relaciones: **Libro N-N Autor** (vía `LibroAutor`), **Préstamo N-1 Socio**, **Préstamo N-1 Libro**.

## Instalar y levantar

Requisitos: Python 3.12 o superior.

```bash
# 1. Crear y activar el entorno virtual
python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Levantar la API
fastapi dev main.py
```

La API queda en http://127.0.0.1:8000 y la base se guarda en `biblioteca.db`, que se crea sola. Para empezar de cero, apagar la API y borrar ese archivo.

> En Windows, si `Activate.ps1` da error de "ejecución de scripts deshabilitada", correr antes:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

### Documentación interactiva (Swagger)

**http://127.0.0.1:8000/docs**: todos los endpoints agrupados por entidad, con **Try it out** para probarlos.

### Datos de ejemplo

Si la base está vacía, al arrancar se cargan:

| Libro | Stock | Autores |
|---|---|---|
| 1 · Ficciones | 3 | Borges |
| 2 · Seis problemas para don Isidro Parodi | 1 | Borges, Bioy Casares |
| 3 · Rayuela | 0 | Cortázar |

| Socio | Estado |
|---|---|
| 1 · Lucía Fernández | activo |
| 2 · Martín Rossi | **inactivo** |

## Endpoints

| Método | Ruta | Descripción | Códigos |
|---|---|---|---|
| POST / GET | `/autores` | Alta / listado | 201, 422 / 200 |
| GET / PATCH / DELETE | `/autores/{id}` | Consulta / modificación / baja | 200, 204, 404 |
| POST / GET | `/libros` | Alta / listado (incluye autores) | 201, 409, 422 / 200 |
| GET | `/libros?disponibles=true` | Libros con stock > 0 (`false`: sin stock) | 200 |
| GET / PATCH / DELETE | `/libros/{id}` | Consulta / modificación / baja | 200, 204, 404, 409 |
| POST | `/libros/{id}/autores/{autor_id}` | Asocia un autor al libro | 201, 404, 409 |
| DELETE | `/libros/{id}/autores/{autor_id}` | Quita la asociación | 200, 404 |
| POST / GET | `/socios` | Alta / listado | 201, 409, 422 / 200 |
| GET / PATCH / DELETE | `/socios/{id}` | Consulta / modificación / baja | 200, 204, 404, 409 |
| GET | `/socios/{id}/prestamos?activos=true` | Préstamos activos del socio (`false`: devueltos) | 200, 404 |
| POST | `/prestamos` | Registra un préstamo | 201, 403, 404, 409 |
| GET | `/prestamos?activos=true` | Lista préstamos | 200 |
| GET | `/prestamos/{id}` | Un préstamo | 200, 404 |
| POST | `/prestamos/{id}/devolucion` | Registra la devolución | 200, 404, 409, 422 |

Ejemplo de préstamo: `POST /prestamos` con `{"socio_id": 1, "libro_id": 1}`.
`fecha_prestamo` (en el préstamo) y `fecha_devolucion` (en la devolución) son **opcionales**; si no se mandan se usa la fecha de hoy. Sirven para probar las multas sin esperar 14 días.

## Reglas de negocio

| # | Regla | Error | Dónde |
|---|---|---|---|
| 1 | Un socio no puede tener más de 3 préstamos activos | 409 | `services/prestamos.py` |
| 2 | No se presta un libro sin stock; al prestar se descuenta 1 | 409 | `services/prestamos.py` |
| 3 | Un socio inactivo no puede pedir préstamos | 403 | `services/prestamos.py` |
| 4 | `fecha_vencimiento = fecha_prestamo + 14 días` | — | `services/prestamos.py` |
| 5 | Al devolver se repone el stock y la multa es $100 × días de atraso | — | `services/prestamos.py` |
| 6 | No se puede devolver un préstamo ya devuelto | 409 | `services/prestamos.py` |
| 7 | Recurso inexistente | 404 | todos los services |
| 8 | ISBN o email duplicado (en alta y en modificación) | 409 | `services/libros.py`, `services/socios.py` |

Decisiones adicionales:

- No se puede borrar un libro ni un socio que tenga préstamos registrados (409): se perdería el historial. A un socio se lo puede marcar `activo: false`.
- Al borrar un autor, se borran sus asociaciones con libros.
- El email se guarda en minúsculas, así `Lucia@email.com` y `lucia@email.com` cuentan como duplicados.
- Una devolución con fecha anterior al préstamo se rechaza con 422.
- El stock no puede ser negativo: lo valida el esquema (422) y además la base de datos (`CHECK stock >= 0`).

## Tests

Con el entorno virtual activado:

```bash
pytest
```

Usa una base **en memoria** (no toca `biblioteca.db`) y muestra el reporte de cobertura al final (configurado en `pytest.ini`). Cobertura actual: **98 %**, con 54 tests.

| Archivo | Qué prueba |
|---|---|
| `tests/test_prestamos.py` | Reglas 1 a 7: un caso feliz y uno de error por regla |
| `tests/test_libros_autores.py` | CRUD de autores y libros, relación N-N, `disponibles`, regla 8 (ISBN) |
| `tests/test_socios.py` | CRUD de socios, regla 8 (email) |
| `tests/test_services.py` | Cálculo de multa y vencimiento sin HTTP, datos de ejemplo |

Para ver qué líneas quedan sin cubrir en HTML: `pytest --cov-report=html` y abrir `htmlcov/index.html`.
