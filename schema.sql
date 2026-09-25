PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS usuario (
  id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
  correo TEXT NOT NULL UNIQUE COLLATE NOCASE,
  password_hash TEXT NOT NULL,
  rol TEXT NOT NULL CHECK (rol IN ('ADMINISTRADOR', 'RECICLADOR'))
);

CREATE TABLE IF NOT EXISTS administrador (
  id_administrador INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL,
  id_usuario INTEGER NOT NULL UNIQUE REFERENCES usuario(id_usuario) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS reciclador (
  id_reciclador INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL,
  id_usuario INTEGER NOT NULL UNIQUE REFERENCES usuario(id_usuario) ON DELETE RESTRICT,
  id_administrador INTEGER NOT NULL REFERENCES administrador(id_administrador) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS empresa_afiliada (
  id_empresa INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL,
  direccion TEXT NOT NULL,
  contacto TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tipo_material (
  id_material INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre_material TEXT NOT NULL,
  porcentaje_meta REAL NOT NULL CHECK (porcentaje_meta >= 0 AND porcentaje_meta <= 100)
);

CREATE TABLE IF NOT EXISTS recoleccion (
  id_recoleccion INTEGER PRIMARY KEY AUTOINCREMENT,
  fecha TEXT NOT NULL,
  cantidad_kg REAL NOT NULL CHECK (cantidad_kg > 0),
  id_reciclador INTEGER NOT NULL REFERENCES reciclador(id_reciclador) ON DELETE RESTRICT,
  id_empresa INTEGER NOT NULL REFERENCES empresa_afiliada(id_empresa) ON DELETE RESTRICT,
  id_material INTEGER NOT NULL REFERENCES tipo_material(id_material) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS sesiones (
  token_hash TEXT PRIMARY KEY,
  id_usuario INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
  expira_en INTEGER NOT NULL
);

CREATE TRIGGER IF NOT EXISTS administrador_role_check
BEFORE INSERT ON administrador
WHEN COALESCE((SELECT rol FROM usuario WHERE id_usuario = NEW.id_usuario), '') <> 'ADMINISTRADOR'
BEGIN SELECT RAISE(ABORT, 'El perfil requiere un usuario ADMINISTRADOR'); END;

CREATE TRIGGER IF NOT EXISTS reciclador_role_check
BEFORE INSERT ON reciclador
WHEN COALESCE((SELECT rol FROM usuario WHERE id_usuario = NEW.id_usuario), '') <> 'RECICLADOR'
BEGIN SELECT RAISE(ABORT, 'El perfil requiere un usuario RECICLADOR'); END;

CREATE TRIGGER IF NOT EXISTS usuario_role_update_check
BEFORE UPDATE OF rol ON usuario
WHEN (EXISTS (SELECT 1 FROM administrador WHERE id_usuario = OLD.id_usuario) AND NEW.rol <> 'ADMINISTRADOR')
  OR (EXISTS (SELECT 1 FROM reciclador WHERE id_usuario = OLD.id_usuario) AND NEW.rol <> 'RECICLADOR')
BEGIN SELECT RAISE(ABORT, 'El rol no coincide con el perfil operativo'); END;

CREATE INDEX IF NOT EXISTS idx_recoleccion_fecha ON recoleccion(fecha);
CREATE INDEX IF NOT EXISTS idx_recoleccion_reciclador ON recoleccion(id_reciclador);
CREATE INDEX IF NOT EXISTS idx_recoleccion_empresa ON recoleccion(id_empresa);
CREATE INDEX IF NOT EXISTS idx_recoleccion_material ON recoleccion(id_material);
CREATE INDEX IF NOT EXISTS idx_sesiones_expira ON sesiones(expira_en);
