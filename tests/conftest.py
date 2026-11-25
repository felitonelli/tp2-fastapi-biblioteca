import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from database import get_session
from main import app


@pytest.fixture(name="session")
def session_fixture():
    # Base en memoria: cada test arranca con una base vacía
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.fixture(name="client")
def client_fixture(session: Session):
    app.dependency_overrides[get_session] = lambda: session
    # Sin "with": no corre el lifespan, así no toca biblioteca.db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def crear_autor(client: TestClient):
    def _crear(nombre="Jorge Luis Borges", nacionalidad="Argentina"):
        res = client.post("/autores", json={"nombre": nombre, "nacionalidad": nacionalidad})
        assert res.status_code == 201
        return res.json()
    return _crear


@pytest.fixture
def crear_libro(client: TestClient):
    contador = {"n": 0}

    def _crear(stock=2, titulo="Ficciones", anio=1944, isbn=None):
        contador["n"] += 1
        isbn = isbn or f"978-0-00-00000{contador['n']}"
        res = client.post("/libros", json={"titulo": titulo, "isbn": isbn, "stock": stock, "anio": anio})
        assert res.status_code == 201
        return res.json()
    return _crear


@pytest.fixture
def crear_socio(client: TestClient):
    contador = {"n": 0}

    def _crear(activo=True, nombre="Lucía", email=None):
        contador["n"] += 1
        email = email or f"socio{contador['n']}@email.com"
        res = client.post("/socios", json={"nombre": nombre, "email": email, "activo": activo})
        assert res.status_code == 201
        return res.json()
    return _crear


@pytest.fixture
def prestar(client: TestClient):
    def _prestar(socio_id, libro_id, fecha=None):
        body = {"socio_id": socio_id, "libro_id": libro_id}
        if fecha:
            body["fecha_prestamo"] = fecha
        return client.post("/prestamos", json=body)
    return _prestar
