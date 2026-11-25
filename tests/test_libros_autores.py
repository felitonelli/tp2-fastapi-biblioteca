"""CRUD de autores y libros, relación N-N y regla 8 (ISBN duplicado)."""


# --- Autores ---

def test_crud_autor(client, crear_autor):
    autor = crear_autor("Borges", "Argentina")
    assert client.get("/autores").json() == [autor]
    assert client.get(f"/autores/{autor['id']}").json() == autor

    res = client.patch(f"/autores/{autor['id']}", json={"nombre": "Jorge Luis Borges"})
    assert res.json() == {**autor, "nombre": "Jorge Luis Borges"}

    assert client.delete(f"/autores/{autor['id']}").status_code == 204
    assert client.get(f"/autores/{autor['id']}").status_code == 404


def test_autor_inexistente_404(client):
    assert client.get("/autores/999").status_code == 404
    assert client.patch("/autores/999", json={"nombre": "x"}).status_code == 404
    assert client.delete("/autores/999").status_code == 404


def test_autor_datos_invalidos_422(client):
    assert client.post("/autores", json={"nombre": "", "nacionalidad": "AR"}).status_code == 422
    assert client.post("/autores", json={"nombre": "Sin nacionalidad"}).status_code == 422


# --- Libros ---

def test_crud_libro(client, crear_libro):
    libro = crear_libro(stock=3, titulo="Ficciones", isbn="111")
    assert libro["autores"] == []
    assert client.get(f"/libros/{libro['id']}").json() == libro

    res = client.patch(f"/libros/{libro['id']}", json={"stock": 5, "anio": 1956})
    assert res.json()["stock"] == 5 and res.json()["anio"] == 1956

    assert client.delete(f"/libros/{libro['id']}").status_code == 204
    assert client.get(f"/libros/{libro['id']}").status_code == 404


def test_libro_inexistente_404(client):
    assert client.get("/libros/999").status_code == 404
    assert client.patch("/libros/999", json={"stock": 1}).status_code == 404
    assert client.delete("/libros/999").status_code == 404


def test_stock_negativo_422(client, crear_libro):
    res = client.post("/libros", json={"titulo": "X", "isbn": "1", "stock": -1, "anio": 2000})
    assert res.status_code == 422
    libro = crear_libro()
    assert client.patch(f"/libros/{libro['id']}", json={"stock": -5}).status_code == 422


def test_regla8_isbn_duplicado_409(client, crear_libro):
    crear_libro(isbn="978-1")
    res = client.post("/libros", json={"titulo": "Otro", "isbn": "978-1", "stock": 1, "anio": 2000})
    assert res.status_code == 409
    assert "ISBN" in res.json()["detail"]


def test_regla8_isbn_duplicado_al_modificar_409(client, crear_libro):
    crear_libro(isbn="978-1")
    libro = crear_libro(isbn="978-2")
    assert client.patch(f"/libros/{libro['id']}", json={"isbn": "978-1"}).status_code == 409
    # cambiarle el ISBN por el mismo que ya tiene no es duplicado
    assert client.patch(f"/libros/{libro['id']}", json={"isbn": "978-2"}).status_code == 200


def test_libros_disponibles(client, crear_libro):
    con_stock = crear_libro(stock=2)
    sin_stock = crear_libro(stock=0)
    todos = client.get("/libros").json()
    assert len(todos) == 2
    disponibles = client.get("/libros", params={"disponibles": True}).json()
    assert [l["id"] for l in disponibles] == [con_stock["id"]]
    agotados = client.get("/libros", params={"disponibles": False}).json()
    assert [l["id"] for l in agotados] == [sin_stock["id"]]


def test_no_se_borra_libro_con_prestamos_409(client, crear_libro, crear_socio, prestar):
    libro = crear_libro()
    prestar(crear_socio()["id"], libro["id"])
    assert client.delete(f"/libros/{libro['id']}").status_code == 409


# --- Relación N-N Libro / Autor ---

def test_asociar_autores_a_libro(client, crear_libro, crear_autor):
    libro = crear_libro(titulo="Seis problemas para don Isidro Parodi")
    borges = crear_autor("Borges")
    bioy = crear_autor("Bioy Casares")

    res = client.post(f"/libros/{libro['id']}/autores/{borges['id']}")
    assert res.status_code == 201
    client.post(f"/libros/{libro['id']}/autores/{bioy['id']}")

    # el libro devuelve sus autores
    autores = client.get(f"/libros/{libro['id']}").json()["autores"]
    assert {a["nombre"] for a in autores} == {"Borges", "Bioy Casares"}
    # y también al listar
    assert len(client.get("/libros").json()[0]["autores"]) == 2


def test_un_autor_en_varios_libros(client, crear_libro, crear_autor):
    autor = crear_autor()
    l1, l2 = crear_libro(), crear_libro()
    client.post(f"/libros/{l1['id']}/autores/{autor['id']}")
    client.post(f"/libros/{l2['id']}/autores/{autor['id']}")
    assert client.get(f"/libros/{l2['id']}").json()["autores"][0]["id"] == autor["id"]


def test_asociar_autor_dos_veces_409(client, crear_libro, crear_autor):
    libro, autor = crear_libro(), crear_autor()
    client.post(f"/libros/{libro['id']}/autores/{autor['id']}")
    assert client.post(f"/libros/{libro['id']}/autores/{autor['id']}").status_code == 409


def test_asociar_inexistentes_404(client, crear_libro, crear_autor):
    libro, autor = crear_libro(), crear_autor()
    assert client.post(f"/libros/999/autores/{autor['id']}").status_code == 404
    assert client.post(f"/libros/{libro['id']}/autores/999").status_code == 404


def test_desasociar_autor(client, crear_libro, crear_autor):
    libro, autor = crear_libro(), crear_autor()
    client.post(f"/libros/{libro['id']}/autores/{autor['id']}")
    res = client.delete(f"/libros/{libro['id']}/autores/{autor['id']}")
    assert res.status_code == 200 and res.json()["autores"] == []
    assert client.delete(f"/libros/{libro['id']}/autores/{autor['id']}").status_code == 404


def test_borrar_autor_lo_saca_de_sus_libros(client, crear_libro, crear_autor):
    libro, autor = crear_libro(), crear_autor()
    client.post(f"/libros/{libro['id']}/autores/{autor['id']}")
    client.delete(f"/autores/{autor['id']}")
    assert client.get(f"/libros/{libro['id']}").json()["autores"] == []
