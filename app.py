"""Recycling management application: stdlib HTTP server + SQLite."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from datetime import date, datetime, timedelta
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("RECICLAJE_DB", ROOT / "data" / "reciclaje.sqlite3"))
SESSION_COOKIE = "reciclaje_session"
SESSION_TTL = 60 * 60 * 12
PBKDF2_ROUNDS = 310_000


@contextmanager
def connect_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    try:
        with db:
            yield db
    finally:
        db.close()


def init_db():
    with connect_db() as db:
        db.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ROUNDS)
    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, rounds, salt, expected = encoded.split("$")
        if scheme != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(rounds)).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def bootstrap_admin(email: str, password: str, name: str):
    if len(password) < 12:
        raise ValueError("La contraseña inicial debe tener al menos 12 caracteres.")
    email = email.strip().lower()
    if "@" not in email:
        raise ValueError("El correo no tiene un formato válido.")
    init_db()
    with connect_db() as db:
        if db.execute("SELECT 1 FROM usuario WHERE correo = ?", (email,)).fetchone():
            raise ValueError("Ya existe un usuario con ese correo.")
        cursor = db.execute("INSERT INTO usuario(correo, password_hash, rol) VALUES(?, ?, 'ADMINISTRADOR')",
                            (email, hash_password(password)))
        db.execute("INSERT INTO administrador(nombre, id_usuario) VALUES(?, ?)", (name.strip(), cursor.lastrowid))


class APIError(Exception):
    def __init__(self, status: int, message: str):
        self.status, self.message = status, message


class Handler(BaseHTTPRequestHandler):
    server_version = "Reciclaje/1.0"

    def log_message(self, fmt, *args):
        print(f"{self.log_date_time_string()} {self.address_string()} {fmt % args}")

    def _send(self, status, body=None, content_type="application/json; charset=utf-8", headers=None):
        # Finish a successful API transaction before the client can observe its response.
        connection = getattr(self, "_api_db", None)
        if connection is not None and status < 400 and self.path.startswith("/api/"):
            connection.commit()
        data = body if isinstance(body, bytes) else (json.dumps(body, ensure_ascii=False).encode() if content_type.startswith("application/json") else str(body or "").encode())
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("Cache-Control", "no-store" if self.path.startswith("/api") else "no-cache")
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

    def _json_body(self):
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size > 1_000_000:
                raise APIError(413, "Solicitud demasiado grande.")
            payload = json.loads(self.rfile.read(size) or b"{}")
            if not isinstance(payload, dict):
                raise APIError(400, "El cuerpo debe ser un objeto JSON.")
            return payload
        except json.JSONDecodeError:
            raise APIError(400, "JSON inválido.")

    def _session(self, db):
        jar = cookies.SimpleCookie(self.headers.get("Cookie", ""))
        item = jar.get(SESSION_COOKIE)
        if not item:
            return None
        row = db.execute("""SELECT u.id_usuario, u.correo, u.rol, a.id_administrador,
                                  r.id_reciclador, r.nombre
                           FROM sesiones s JOIN usuario u ON u.id_usuario=s.id_usuario
                           LEFT JOIN administrador a ON a.id_usuario=u.id_usuario
                           LEFT JOIN reciclador r ON r.id_usuario=u.id_usuario
                           WHERE s.token_hash=? AND s.expira_en>?""",
                         (hashlib.sha256(item.value.encode()).hexdigest(), int(time.time()))).fetchone()
        return dict(row) if row else None

    def _require(self, db, role=None):
        user = self._session(db)
        if not user:
            raise APIError(401, "Inicia sesión para continuar.")
        if role and user["rol"] != role:
            raise APIError(403, "No tienes permiso para realizar esta operación.")
        return user

    def _query_filters(self):
        params = parse_qs(urlparse(self.path).query)
        parts, values = [], []
        for key, column in (("year", "strftime('%Y', r.fecha)"), ("month", "strftime('%m', r.fecha)"),
                            ("empresa", "r.id_empresa"), ("reciclador", "r.id_reciclador"), ("material", "r.id_material")):
            value = params.get(key, [""])[0]
            if value:
                if key in ("year", "month") and not value.isdigit():
                    raise APIError(400, f"Filtro {key} inválido.")
                if key == "month" and not 1 <= int(value) <= 12:
                    raise APIError(400, "El mes debe estar entre 1 y 12.")
                parts.append(f"{column}=?")
                values.append(value.zfill(2) if key == "month" else value)
        return (" WHERE " + " AND ".join(parts) if parts else ""), values

    def _dispatch(self):
        parsed = urlparse(self.path)
        path, method = parsed.path, self.command
        with connect_db() as db:
            self._api_db = db
            if path == "/api/auth/login" and method == "POST":
                data = self._json_body()
                email, password = str(data.get("correo", "")).strip().lower(), str(data.get("contrasena", ""))
                row = db.execute("SELECT * FROM usuario WHERE correo=?", (email,)).fetchone()
                if not row or not verify_password(password, row["password_hash"]):
                    raise APIError(401, "Correo o contraseña incorrectos.")
                token = secrets.token_urlsafe(32)
                db.execute("DELETE FROM sesiones WHERE expira_en<=?", (int(time.time()),))
                db.execute("INSERT INTO sesiones(token_hash,id_usuario,expira_en) VALUES(?,?,?)",
                           (hashlib.sha256(token.encode()).hexdigest(), row["id_usuario"], int(time.time()) + SESSION_TTL))
                cookie = f"{SESSION_COOKIE}={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age={SESSION_TTL}"
                self._send(200, {"ok": True, "rol": row["rol"]}, headers={"Set-Cookie": cookie})
                return
            if path == "/api/auth/logout" and method == "POST":
                jar = cookies.SimpleCookie(self.headers.get("Cookie", ""))
                item = jar.get(SESSION_COOKIE)
                if item:
                    db.execute("DELETE FROM sesiones WHERE token_hash=?", (hashlib.sha256(item.value.encode()).hexdigest(),))
                self._send(200, {"ok": True}, headers={"Set-Cookie": f"{SESSION_COOKIE}=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0"})
                return
            if path == "/api/auth/me" and method == "GET":
                user = self._session(db)
                if not user:
                    raise APIError(401, "Sesión no válida.")
                self._send(200, {"usuario": user})
                return

            user = self._session(db)
            if path == "/api/recolectores" and method == "GET":
                self._require(db, "ADMINISTRADOR")
                rows = db.execute("""SELECT r.id_reciclador,r.nombre,u.correo,a.nombre AS administrador,
                                    (SELECT COUNT(*) FROM recoleccion x WHERE x.id_reciclador=r.id_reciclador) AS recolecciones
                                    FROM reciclador r JOIN usuario u ON u.id_usuario=r.id_usuario
                                    JOIN administrador a ON a.id_administrador=r.id_administrador ORDER BY r.nombre""").fetchall()
                self._send(200, {"items": [dict(x) for x in rows]})
                return
            if path == "/api/recolectores" and method == "POST":
                user = self._require(db, "ADMINISTRADOR")
                data = self._json_body()
                name, email, password = str(data.get("nombre", "")).strip(), str(data.get("correo", "")).strip().lower(), str(data.get("contrasena", ""))
                if not name or "@" not in email or len(password) < 12:
                    raise APIError(400, "Indica nombre, correo válido y contraseña de al menos 12 caracteres.")
                cursor = db.execute("INSERT INTO usuario(correo,password_hash,rol) VALUES(?,?,'RECICLADOR')", (email, hash_password(password)))
                db.execute("INSERT INTO reciclador(nombre,id_usuario,id_administrador) VALUES(?,?,?)", (name, cursor.lastrowid, user["id_administrador"]))
                self._send(201, {"ok": True})
                return
            if path.startswith("/api/recolectores/") and method in ("GET", "PUT", "DELETE"):
                user = self._require(db, "ADMINISTRADOR")
                rid = self._id(path.split("/")[-1])
                found = db.execute("SELECT * FROM reciclador WHERE id_reciclador=?", (rid,)).fetchone()
                if not found:
                    raise APIError(404, "Reciclador no encontrado.")
                if method == "GET":
                    self._send(200, {"item": dict(found)})
                elif method == "PUT":
                    data = self._json_body(); name = str(data.get("nombre", "")).strip()
                    if not name: raise APIError(400, "El nombre es obligatorio.")
                    db.execute("UPDATE reciclador SET nombre=? WHERE id_reciclador=?", (name, rid)); self._send(200, {"ok": True})
                else:
                    if db.execute("SELECT 1 FROM recoleccion WHERE id_reciclador=? LIMIT 1", (rid,)).fetchone():
                        raise APIError(409, "No se puede eliminar: el reciclador tiene recolecciones históricas.")
                    db.execute("DELETE FROM reciclador WHERE id_reciclador=?", (rid,)); db.execute("DELETE FROM usuario WHERE id_usuario=?", (found["id_usuario"],)); self._send(200, {"ok": True})
                return
            if path in ("/api/empresas", "/api/materiales"):
                is_company = path.endswith("empresas")
                table, idcol, cols = (("empresa_afiliada", "id_empresa", "nombre,direccion,contacto") if is_company else ("tipo_material", "id_material", "nombre_material,porcentaje_meta"))
                if method == "GET":
                    self._require(db)
                    rows = db.execute(f"SELECT {idcol},{cols} FROM {table} ORDER BY 2").fetchall()
                    self._send(200, {"items": [dict(x) for x in rows]}); return
                if method == "POST":
                    self._require(db, "ADMINISTRADOR")
                    data = self._json_body()
                    if is_company:
                        name = str(data.get("nombre", "")).strip(); address = str(data.get("direccion", "")).strip(); contact = str(data.get("contacto", "")).strip()
                        if not name or not address or not contact: raise APIError(400, "Nombre, dirección y contacto son obligatorios.")
                        db.execute("INSERT INTO empresa_afiliada(nombre,direccion,contacto) VALUES(?,?,?)", (name,address,contact))
                    else:
                        name = str(data.get("nombre_material", "")).strip()
                        try: target = float(data.get("porcentaje_meta"))
                        except (TypeError, ValueError): raise APIError(400, "El porcentaje meta debe ser un número de 0 a 100.")
                        if not name or not 0 <= target <= 100: raise APIError(400, "Nombre obligatorio y porcentaje meta entre 0 y 100.")
                        db.execute("INSERT INTO tipo_material(nombre_material,porcentaje_meta) VALUES(?,?)", (name,target))
                    self._send(201, {"ok": True}); return
                raise APIError(405, "Método no permitido.")
            if path.startswith("/api/empresas/") or path.startswith("/api/materiales/"):
                self._require(db, "ADMINISTRADOR")
                is_company = path.startswith("/api/empresas/")
                table, idcol = (("empresa_afiliada","id_empresa") if is_company else ("tipo_material","id_material"))
                item_id = self._id(path.split("/")[-1])
                if method not in ("PUT", "DELETE"): raise APIError(405, "Método no permitido.")
                if method == "DELETE":
                    try: db.execute(f"DELETE FROM {table} WHERE {idcol}=?", (item_id,))
                    except sqlite3.IntegrityError: raise APIError(409, "No se puede eliminar porque tiene recolecciones asociadas.")
                    self._send(200,{"ok":True}); return
                data = self._json_body()
                try:
                    if is_company:
                        name,direction,contact = (str(data.get(k,"")).strip() for k in ("nombre","direccion","contacto"))
                        if not all((name,direction,contact)): raise APIError(400,"Nombre, dirección y contacto son obligatorios.")
                        db.execute("UPDATE empresa_afiliada SET nombre=?,direccion=?,contacto=? WHERE id_empresa=?",(name,direction,contact,item_id))
                    else:
                        name = str(data.get("nombre_material","")).strip(); pct = float(data.get("porcentaje_meta"))
                        if not name or not 0 <= pct <= 100: raise APIError(400,"Nombre obligatorio y porcentaje meta entre 0 y 100.")
                        db.execute("UPDATE tipo_material SET nombre_material=?,porcentaje_meta=? WHERE id_material=?",(name,pct,item_id))
                except (ValueError,TypeError): raise APIError(400,"Porcentaje meta inválido.")
                self._send(200,{"ok":True}); return
            if path == "/api/recolecciones" and method == "GET":
                user = self._require(db)
                where, args = self._query_filters()
                if user["rol"] == "RECICLADOR":
                    where += (" AND " if where else " WHERE ") + "r.id_reciclador=?"; args.append(user["id_reciclador"])
                rows = db.execute("""SELECT r.id_recoleccion,r.fecha,r.cantidad_kg,r.id_reciclador,
                                    rc.nombre AS reciclador,e.id_empresa,e.nombre AS empresa,
                                    m.id_material,m.nombre_material AS material
                                    FROM recoleccion r JOIN reciclador rc ON rc.id_reciclador=r.id_reciclador
                                    JOIN empresa_afiliada e ON e.id_empresa=r.id_empresa
                                    JOIN tipo_material m ON m.id_material=r.id_material""" + where + " ORDER BY r.fecha DESC,r.id_recoleccion DESC", args).fetchall()
                self._send(200,{"items":[dict(x) for x in rows]}); return
            if path == "/api/recolecciones" and method == "POST":
                user = self._require(db,"RECICLADOR")
                data=self._json_body()
                try:
                    d=date.fromisoformat(str(data.get("fecha",""))); kg=float(data.get("cantidad_kg")); eid=int(data.get("id_empresa")); mid=int(data.get("id_material"))
                except (ValueError,TypeError): raise APIError(400,"Fecha, empresa, material y cantidad válidos son obligatorios.")
                if not math_finite_positive(kg): raise APIError(400,"La cantidad debe ser mayor que cero.")
                if not db.execute("SELECT 1 FROM empresa_afiliada WHERE id_empresa=?",(eid,)).fetchone(): raise APIError(400,"La empresa seleccionada no existe.")
                if not db.execute("SELECT 1 FROM tipo_material WHERE id_material=?",(mid,)).fetchone(): raise APIError(400,"El material seleccionado no existe.")
                db.execute("INSERT INTO recoleccion(fecha,cantidad_kg,id_reciclador,id_empresa,id_material) VALUES(?,?,?,?,?)",(d.isoformat(),kg,user["id_reciclador"],eid,mid))
                self._send(201,{"ok":True}); return
            if path == "/api/indicadores" and method == "GET":
                user=self._require(db,"ADMINISTRADOR"); where,args=self._query_filters()
                total=db.execute("SELECT COALESCE(SUM(r.cantidad_kg),0) total,COUNT(*) n FROM recoleccion r"+where,args).fetchone()
                materials=db.execute("""SELECT m.id_material,m.nombre_material,COALESCE(SUM(r.cantidad_kg),0) cantidad_kg
                                         FROM tipo_material m LEFT JOIN recoleccion r ON r.id_material=m.id_material"""+
                                     (where.replace(" WHERE "," AND ") if where else "")+" GROUP BY m.id_material ORDER BY cantidad_kg DESC",args).fetchall()
                month_rows=db.execute("SELECT strftime('%Y-%m',r.fecha) mes,SUM(r.cantidad_kg) cantidad_kg FROM recoleccion r"+where+" GROUP BY mes ORDER BY mes DESC LIMIT 12",args).fetchall()
                recycler_count=db.execute("SELECT COUNT(*) n FROM reciclador").fetchone()["n"]
                self._send(200,{"total_kg":total["total"],"recolecciones":total["n"],"recicladores_registrados":recycler_count,
                                "ingresos":None,"ganancias":None,"materiales":[dict(x) for x in materials],"mensual":[dict(x) for x in month_rows],
                                "notas":{"ingresos":"Pendiente de definición: no existe fórmula en la especificación.","ganancias":"Pendiente de definición: no existe fórmula en la especificación.","porcentaje_meta":"Se almacena y valida; su uso está pendiente de definición.","recicladores_activos":"Criterio de actividad pendiente de definición; se muestra el conteo de recicladores registrados."}})
                return
            if path == "/api/reportes/empresas" and method == "GET":
                self._require(db,"ADMINISTRADOR"); params=parse_qs(parsed.query)
                month=params.get("month",[""])[0]; year=params.get("year",[""])[0]; eid=params.get("empresa",[""])[0]
                if not (month.isdigit() and year.isdigit() and eid.isdigit() and 1<=int(month)<=12): raise APIError(400,"Indica mes, año y empresa válidos.")
                company=db.execute("SELECT id_empresa,nombre FROM empresa_afiliada WHERE id_empresa=?",(int(eid),)).fetchone()
                if not company: raise APIError(404,"Empresa no encontrada.")
                items=db.execute("""SELECT m.nombre_material material,SUM(r.cantidad_kg) cantidad_kg,COUNT(*) recolecciones
                                     FROM recoleccion r JOIN tipo_material m ON m.id_material=r.id_material
                                     WHERE r.id_empresa=? AND strftime('%Y',r.fecha)=? AND strftime('%m',r.fecha)=?
                                     GROUP BY m.id_material ORDER BY m.nombre_material""",(int(eid),year,month.zfill(2))).fetchall()
                total=sum(row["cantidad_kg"] for row in items)
                self._send(200,{"empresa":dict(company),"periodo":f"{year}-{month.zfill(2)}","total_kg":total,"items":[dict(x) for x in items],"origen":"Calculado exclusivamente desde RECOLECCION."});return
            if path.startswith("/api/resumen") and method == "GET":
                user=self._require(db,"RECICLADOR"); params=parse_qs(parsed.query)
                month=params.get("month",[str(date.today().month)])[0]; year=params.get("year",[str(date.today().year)])[0]
                if not (month.isdigit() and year.isdigit() and 1<=int(month)<=12): raise APIError(400,"Mes o año inválido.")
                rows=db.execute("""SELECT m.nombre_material material,SUM(r.cantidad_kg) cantidad_kg,COUNT(*) recolecciones
                                     FROM recoleccion r JOIN tipo_material m ON m.id_material=r.id_material
                                     WHERE r.id_reciclador=? AND strftime('%Y',r.fecha)=? AND strftime('%m',r.fecha)=?
                                     GROUP BY m.id_material ORDER BY m.nombre_material""",(user["id_reciclador"],year,month.zfill(2))).fetchall()
                self._send(200,{"periodo":f"{year}-{month.zfill(2)}","total_kg":sum(x["cantidad_kg"] for x in rows),"items":[dict(x) for x in rows],"ganancia":None,"nota":"Fórmula de ganancia pendiente de definición."});return
            raise APIError(404,"Ruta no encontrada.")

    @staticmethod
    def _id(value):
        try: return int(value)
        except ValueError: raise APIError(400,"Identificador inválido.")

    def do_GET(self):
        if self.path.startswith("/api/"):
            self._api()
        else:
            filename="index.html" if self.path in ("/","/index.html") else self.path.lstrip("/")
            candidate=(ROOT/"static"/filename).resolve()
            if ROOT.joinpath("static").resolve() not in candidate.parents or not candidate.is_file():
                self._send(404,"No encontrado","text/plain; charset=utf-8"); return
            mime="text/css; charset=utf-8" if candidate.suffix==".css" else "application/javascript; charset=utf-8" if candidate.suffix==".js" else "text/html; charset=utf-8"
            self._send(200,candidate.read_bytes(),mime)

    def do_POST(self): self._api()
    def do_PUT(self): self._api()
    def do_DELETE(self): self._api()

    def _api(self):
        try: self._dispatch()
        except APIError as error: self._send(error.status,{"error":error.message})
        except sqlite3.IntegrityError as error:
            message="El correo ya está registrado." if "usuario.correo" in str(error) else "La operación viola una relación o restricción de datos."
            self._send(409,{"error":message})
        except Exception as error:
            print(f"Error interno: {error!r}")
            self._send(500,{"error":"Error interno del servidor."})


def math_finite_positive(number):
    import math
    return math.isfinite(number) and number > 0


def main():
    parser=argparse.ArgumentParser(description="Sistema Digital de Gestión de Reciclaje")
    sub=parser.add_subparsers(dest="command")
    sub.add_parser("init-db",help="Crear esquema de base de datos")
    admin=sub.add_parser("create-admin",help="Crear administrador inicial")
    admin.add_argument("--nombre",required=True); admin.add_argument("--correo",required=True)
    admin.add_argument("--contrasena",required=True,help="Al menos 12 caracteres")
    run=sub.add_parser("serve",help="Iniciar servidor web")
    run.add_argument("--host",default="127.0.0.1"); run.add_argument("--port",type=int,default=8000)
    args=parser.parse_args()
    if args.command=="init-db": init_db(); print(f"Base de datos lista: {DB_PATH}")
    elif args.command=="create-admin": bootstrap_admin(args.correo,args.contrasena,args.nombre); print("Administrador creado.")
    else:
        init_db(); host=getattr(args,"host","127.0.0.1"); port=getattr(args,"port",8000)
        server=ThreadingHTTPServer((host,port),Handler)
        print(f"Sistema disponible en http://{host}:{port} — Ctrl+C para detener")
        try: server.serve_forever()
        except KeyboardInterrupt: pass
        finally: server.server_close()


if __name__=="__main__": main()
