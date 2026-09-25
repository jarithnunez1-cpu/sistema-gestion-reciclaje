"""End-to-end acceptance checks using only the Python standard library."""
import json
import threading
import unittest
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path
from tempfile import TemporaryDirectory

import app


class RecyclingSystemTests(unittest.TestCase):
    def setUp(self):
        self.old_rounds = app.PBKDF2_ROUNDS
        app.PBKDF2_ROUNDS = 10_000  # Keep the suite fast; production retains the default cost.
        self.temp = TemporaryDirectory()
        app.DB_PATH = Path(self.temp.name) / "test.sqlite3"
        app.init_db()
        app.bootstrap_admin("admin@example.test", "Admin-password-2026!", "Administración")
        self.server = app.ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
        self.login("admin@example.test", "Admin-password-2026!")

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()
        app.PBKDF2_ROUNDS = self.old_rounds

    def call(self, path, method="GET", data=None):
        body = None if data is None else json.dumps(data).encode()
        request = urllib.request.Request(self.base + path, data=body, method=method,
                                         headers={"Content-Type": "application/json"})
        try:
            with self.opener.open(request) as response:
                return response.status, json.loads(response.read() or b"{}")
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read() or b"{}")

    def login(self, email, password):
        return self.call("/api/auth/login", "POST", {"correo": email, "contrasena": password})

    def fixtures(self):
        self.call("/api/empresas", "POST", {"nombre": "Empresa Norte", "direccion": "Calle 1", "contacto": "123"})
        self.call("/api/materiales", "POST", {"nombre_material": "Cartón", "porcentaje_meta": 25})
        self.call("/api/recolectores", "POST", {"nombre": "Rosa", "correo": "rosa@example.test", "contrasena": "Recycled-password-26!"})
        with app.connect_db() as db:
            return db.execute("SELECT id_empresa FROM empresa_afiliada").fetchone()[0], db.execute("SELECT id_material FROM tipo_material").fetchone()[0], db.execute("SELECT id_reciclador FROM reciclador").fetchone()[0]

    def test_one_login_routes_both_defined_roles(self):
        self.assertEqual(self.login("admin@example.test", "Admin-password-2026!")[1]["rol"], "ADMINISTRADOR")
        self.fixtures()
        self.call("/api/auth/logout", "POST")
        self.assertEqual(self.login("rosa@example.test", "Recycled-password-26!")[1]["rol"], "RECICLADOR")

    def test_role_guards_reject_admin_collection_creation_and_anonymous_access(self):
        self.call("/api/auth/logout", "POST")
        self.assertEqual(self.call("/api/recolecciones")[0], 401)
        self.login("admin@example.test", "Admin-password-2026!")
        self.assertEqual(self.call("/api/recolecciones", "POST", {})[0], 403)

    def test_recycler_can_read_selection_catalogs_but_not_admin_management(self):
        self.fixtures()
        self.call("/api/auth/logout", "POST")
        self.login("rosa@example.test", "Recycled-password-26!")
        self.assertEqual(self.call("/api/empresas")[0], 200)
        self.assertEqual(self.call("/api/materiales")[0], 200)
        self.assertEqual(self.call("/api/recolectores")[0], 403)
        self.assertEqual(self.call("/api/empresas", "POST", {"nombre":"Otro","direccion":"A","contacto":"B"})[0], 403)

    def test_recycler_validation_and_identity_binding(self):
        eid, mid, rid = self.fixtures()
        self.call("/api/auth/logout", "POST")
        self.login("rosa@example.test", "Recycled-password-26!")
        base = {"fecha": "2026-09-25", "id_empresa": eid, "id_material": mid, "cantidad_kg": 4}
        for invalid in ({**base, "cantidad_kg": 0}, {**base, "id_empresa": ""}, {**base, "id_material": ""}, {**base, "fecha": ""}):
            self.assertEqual(self.call("/api/recolecciones", "POST", invalid)[0], 400)
        self.assertEqual(self.call("/api/recolecciones", "POST", {**base, "id_reciclador": 9999})[0], 201)
        _, data = self.call("/api/recolecciones")
        self.assertEqual(data["items"][0]["id_reciclador"], rid)

    def test_material_percentage_validation_and_historic_recycler_retention(self):
        self.assertEqual(self.call("/api/materiales", "POST", {"nombre_material": "Inválido", "porcentaje_meta": 101})[0], 400)
        eid, mid, rid = self.fixtures()
        self.call("/api/auth/logout", "POST")
        self.login("rosa@example.test", "Recycled-password-26!")
        self.call("/api/recolecciones", "POST", {"fecha": "2026-09-25", "id_empresa": eid, "id_material": mid, "cantidad_kg": 7.5})
        self.call("/api/auth/logout", "POST")
        self.login("admin@example.test", "Admin-password-2026!")
        self.assertEqual(self.call(f"/api/recolectores/{rid}", "DELETE")[0], 409)

    def test_dynamic_indicators_and_company_monthly_report(self):
        eid, mid, _ = self.fixtures()
        self.call("/api/auth/logout", "POST")
        self.login("rosa@example.test", "Recycled-password-26!")
        self.call("/api/recolecciones", "POST", {"fecha": "2026-09-25", "id_empresa": eid, "id_material": mid, "cantidad_kg": 12.25})
        self.call("/api/auth/logout", "POST")
        self.login("admin@example.test", "Admin-password-2026!")
        _, indicators = self.call("/api/indicadores?year=2026&month=09")
        self.assertEqual(indicators["total_kg"], 12.25)
        _, report = self.call(f"/api/reportes/empresas?empresa={eid}&year=2026&month=09")
        self.assertEqual(report["total_kg"], 12.25)
        self.assertIsNone(indicators["ingresos"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
