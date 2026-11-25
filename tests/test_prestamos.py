"""Un test de caso feliz y uno de error por cada regla de negocio."""


# --- Regla 1: máximo 3 préstamos activos por socio (409) ---

def test_regla1_hasta_tres_prestamos_activos(client, crear_socio, crear_libro, prestar):
    socio = crear_socio()
    libro = crear_libro(stock=10)
    for _ in range(3):
        assert prestar(socio["id"], libro["id"]).status_code == 201


def test_regla1_cuarto_prestamo_activo_409(client, crear_socio, crear_libro, prestar):
    socio = crear_socio()
    libro = crear_libro(stock=10)
    for _ in range(3):
        prestar(socio["id"], libro["id"])
    res = prestar(socio["id"], libro["id"])
    assert res.status_code == 409
    assert "3 préstamos activos" in res.json()["detail"]


def test_regla1_al_devolver_puede_pedir_otro(client, crear_socio, crear_libro, prestar):
    socio = crear_socio()
    libro = crear_libro(stock=10)
    ids = [prestar(socio["id"], libro["id"]).json()["id"] for _ in range(3)]
    client.post(f"/prestamos/{ids[0]}/devolucion")
    assert prestar(socio["id"], libro["id"]).status_code == 201


# --- Regla 2: sin stock no se presta (409); al prestar se descuenta 1 ---

def test_regla2_prestar_descuenta_stock(client, crear_socio, crear_libro, prestar):
    socio = crear_socio()
    libro = crear_libro(stock=2)
    assert prestar(socio["id"], libro["id"]).status_code == 201
    assert client.get(f"/libros/{libro['id']}").json()["stock"] == 1


def test_regla2_libro_sin_stock_409(client, crear_socio, crear_libro, prestar):
    socio = crear_socio()
    libro = crear_libro(stock=0)
    res = prestar(socio["id"], libro["id"])
    assert res.status_code == 409
    assert "stock" in res.json()["detail"]


def test_regla2_se_agota_el_stock(client, crear_socio, crear_libro, prestar):
    libro = crear_libro(stock=1)
    assert prestar(crear_socio()["id"], libro["id"]).status_code == 201
    assert prestar(crear_socio()["id"], libro["id"]).status_code == 409
    assert client.get(f"/libros/{libro['id']}").json()["stock"] == 0


# --- Regla 3: socio inactivo no puede pedir préstamos (403) ---

def test_regla3_socio_activo_puede_pedir(client, crear_socio, crear_libro, prestar):
    assert prestar(crear_socio(activo=True)["id"], crear_libro()["id"]).status_code == 201


def test_regla3_socio_inactivo_403(client, crear_socio, crear_libro, prestar):
    libro = crear_libro(stock=1)
    res = prestar(crear_socio(activo=False)["id"], libro["id"])
    assert res.status_code == 403
    # no se descontó stock
    assert client.get(f"/libros/{libro['id']}").json()["stock"] == 1


def test_regla3_socio_dado_de_baja_despues(client, crear_socio, crear_libro, prestar):
    socio = crear_socio()
    client.patch(f"/socios/{socio['id']}", json={"activo": False})
    assert prestar(socio["id"], crear_libro()["id"]).status_code == 403


# --- Regla 4: vencimiento = fecha de préstamo + 14 días ---

def test_regla4_vencimiento_a_los_14_dias(client, crear_socio, crear_libro, prestar):
    res = prestar(crear_socio()["id"], crear_libro()["id"], fecha="2026-11-01")
    assert res.json()["fecha_prestamo"] == "2026-11-01"
    assert res.json()["fecha_vencimiento"] == "2026-11-15"


def test_regla4_cruza_de_mes_y_anio(client, crear_socio, crear_libro, prestar):
    res = prestar(crear_socio()["id"], crear_libro()["id"], fecha="2026-12-25")
    assert res.json()["fecha_vencimiento"] == "2027-01-08"


def test_regla4_sin_fecha_usa_hoy(client, crear_socio, crear_libro, prestar):
    from datetime import date, timedelta
    res = prestar(crear_socio()["id"], crear_libro()["id"])
    hoy = date.today()
    assert res.json()["fecha_prestamo"] == hoy.isoformat()
    assert res.json()["fecha_vencimiento"] == (hoy + timedelta(days=14)).isoformat()


# --- Regla 5: devolver repone stock y calcula multa ($100 por día de atraso) ---

def test_regla5_devolucion_a_tiempo_sin_multa(client, crear_socio, crear_libro, prestar):
    libro = crear_libro(stock=1)
    prestamo = prestar(crear_socio()["id"], libro["id"], fecha="2026-11-01").json()
    res = client.post(f"/prestamos/{prestamo['id']}/devolucion", json={"fecha_devolucion": "2026-11-15"})
    assert res.status_code == 200
    assert res.json()["multa"] == 0
    assert res.json()["activo"] is False
    assert client.get(f"/libros/{libro['id']}").json()["stock"] == 1  # stock repuesto


def test_regla5_devolucion_con_atraso_cobra_multa(client, crear_socio, crear_libro, prestar):
    prestamo = prestar(crear_socio()["id"], crear_libro()["id"], fecha="2026-11-01").json()
    # vence el 15; se devuelve el 20 → 5 días de atraso
    res = client.post(f"/prestamos/{prestamo['id']}/devolucion", json={"fecha_devolucion": "2026-11-20"})
    assert res.json()["multa"] == 500
    assert res.json()["fecha_devolucion"] == "2026-11-20"


def test_regla5_devolucion_sin_body_usa_hoy(client, crear_socio, crear_libro, prestar):
    prestamo = prestar(crear_socio()["id"], crear_libro()["id"]).json()
    res = client.post(f"/prestamos/{prestamo['id']}/devolucion")
    assert res.status_code == 200
    assert res.json()["multa"] == 0


def test_devolucion_anterior_al_prestamo_422(client, crear_socio, crear_libro, prestar):
    prestamo = prestar(crear_socio()["id"], crear_libro()["id"], fecha="2026-11-10").json()
    res = client.post(f"/prestamos/{prestamo['id']}/devolucion", json={"fecha_devolucion": "2026-11-01"})
    assert res.status_code == 422


# --- Regla 6: no se puede devolver dos veces (409) ---

def test_regla6_doble_devolucion_409(client, crear_socio, crear_libro, prestar):
    libro = crear_libro(stock=1)
    prestamo = prestar(crear_socio()["id"], libro["id"]).json()
    assert client.post(f"/prestamos/{prestamo['id']}/devolucion").status_code == 200
    res = client.post(f"/prestamos/{prestamo['id']}/devolucion")
    assert res.status_code == 409
    # el stock no se repuso dos veces
    assert client.get(f"/libros/{libro['id']}").json()["stock"] == 1


# --- Regla 7: recurso inexistente (404) ---

def test_regla7_prestamo_con_socio_inexistente(client, crear_libro, prestar):
    assert prestar(999, crear_libro()["id"]).status_code == 404


def test_regla7_prestamo_con_libro_inexistente(client, crear_socio, prestar):
    assert prestar(crear_socio()["id"], 999).status_code == 404


def test_regla7_devolver_prestamo_inexistente(client):
    assert client.post("/prestamos/999/devolucion").status_code == 404


def test_regla7_obtener_prestamo(client, crear_socio, crear_libro, prestar):
    prestamo = prestar(crear_socio()["id"], crear_libro()["id"]).json()
    assert client.get(f"/prestamos/{prestamo['id']}").json() == prestamo
    assert client.get("/prestamos/999").status_code == 404


# --- Consultas de préstamos ---

def test_prestamos_activos_del_socio(client, crear_socio, crear_libro, prestar):
    socio = crear_socio()
    otro = crear_socio()
    libro = crear_libro(stock=10)
    p1 = prestar(socio["id"], libro["id"]).json()
    p2 = prestar(socio["id"], libro["id"]).json()
    prestar(otro["id"], libro["id"])
    client.post(f"/prestamos/{p1['id']}/devolucion")

    activos = client.get(f"/socios/{socio['id']}/prestamos", params={"activos": True}).json()
    assert [p["id"] for p in activos] == [p2["id"]]
    devueltos = client.get(f"/socios/{socio['id']}/prestamos", params={"activos": False}).json()
    assert [p["id"] for p in devueltos] == [p1["id"]]
    todos = client.get(f"/socios/{socio['id']}/prestamos").json()
    assert len(todos) == 2


def test_prestamos_de_socio_inexistente_404(client):
    assert client.get("/socios/999/prestamos?activos=true").status_code == 404


def test_listar_prestamos(client, crear_socio, crear_libro, prestar):
    libro = crear_libro(stock=5)
    p1 = prestar(crear_socio()["id"], libro["id"]).json()
    prestar(crear_socio()["id"], libro["id"])
    client.post(f"/prestamos/{p1['id']}/devolucion")
    assert len(client.get("/prestamos").json()) == 2
    assert len(client.get("/prestamos?activos=true").json()) == 1
    assert len(client.get("/prestamos?activos=false").json()) == 1
