"""CRUD de socios y regla 8 (email duplicado)."""


def test_crud_socio(client, crear_socio):
    socio = crear_socio(nombre="Lucía", email="lucia@email.com")
    assert socio["activo"] is True
    assert client.get("/socios").json() == [socio]
    assert client.get(f"/socios/{socio['id']}").json() == socio

    res = client.patch(f"/socios/{socio['id']}", json={"activo": False, "nombre": "Lucía F."})
    assert res.json() == {**socio, "activo": False, "nombre": "Lucía F."}

    assert client.delete(f"/socios/{socio['id']}").status_code == 204
    assert client.get(f"/socios/{socio['id']}").status_code == 404


def test_socio_inexistente_404(client):
    assert client.get("/socios/999").status_code == 404
    assert client.patch("/socios/999", json={"activo": False}).status_code == 404
    assert client.delete("/socios/999").status_code == 404


def test_email_invalido_422(client):
    res = client.post("/socios", json={"nombre": "X", "email": "no-es-un-mail"})
    assert res.status_code == 422


def test_regla8_email_duplicado_409(client, crear_socio):
    crear_socio(email="lucia@email.com")
    res = client.post("/socios", json={"nombre": "Otra", "email": "lucia@email.com"})
    assert res.status_code == 409
    assert "email" in res.json()["detail"]


def test_regla8_email_duplicado_sin_importar_mayusculas(client, crear_socio):
    crear_socio(email="lucia@email.com")
    res = client.post("/socios", json={"nombre": "Otra", "email": "LUCIA@email.com"})
    assert res.status_code == 409


def test_regla8_email_duplicado_al_modificar_409(client, crear_socio):
    crear_socio(email="a@email.com")
    socio = crear_socio(email="b@email.com")
    assert client.patch(f"/socios/{socio['id']}", json={"email": "a@email.com"}).status_code == 409
    assert client.patch(f"/socios/{socio['id']}", json={"email": "B@email.com"}).status_code == 200


def test_no_se_borra_socio_con_prestamos_409(client, crear_socio, crear_libro, prestar):
    socio = crear_socio()
    prestar(socio["id"], crear_libro()["id"])
    assert client.delete(f"/socios/{socio['id']}").status_code == 409
