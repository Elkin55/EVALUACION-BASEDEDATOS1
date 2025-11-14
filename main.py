import os
import base64
import bcrypt
import getpass
import secrets
from datetime import datetime, UTC
from dotenv import load_dotenv
import mysql.connector
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

def b64_encode(b):
    return base64.b64encode(b).decode('utf-8')

def b64_decode(s):
    return base64.b64decode(s.encode('utf-8'))

def hash_password(password):
    h = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return b64_encode(h)

def verify_password(password, stored_b64):
    try:
        stored = b64_decode(stored_b64)
        return bcrypt.checkpw(password.encode('utf-8'), stored)
    except:
        return False

class SistemaAutenticacion:
    def __init__(self):
        self.mysql = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            autocommit=False
        )
        self.mongo = MongoClient(MONGO_URI)
        self.mongo_db = self.mongo["auth_system"]
        self.mongo_users = self.mongo_db["usuarios"]
        self.mongo_logs = self.mongo_db["logs"]
        self.usuario_actual = None

    def asegurar_conexion_mysql(self):
        if not self.mysql.is_connected():
            self.mysql.reconnect()

    def crear_log(self, usuario_identifier, accion, ip="127.0.0.1"):
        self.mongo_logs.insert_one({
            "usuario": usuario_identifier,
            "accion": accion,
            "fecha": datetime.now(UTC),
            "ip": ip
        })

    def registrar_usuario(self):
        self.asegurar_conexion_mysql()
        print("\n--- Registro de Usuario ---")
        username = input("Username: ").strip()
        email = input("Email: ").strip()
        if not username or not email:
            print("Username y email obligatorios.")
            return
        cursor = self.mysql.cursor(dictionary=True)
        cursor.execute("SELECT id FROM usuarios WHERE username = %s OR email = %s", (username, email))
        if cursor.fetchone():
            print("Error: username o email ya existe.")
            cursor.close()
            return
        password = getpass.getpass("Password: ")
        if len(password) < 4:
            print("Password muy corta.")
            return
        rol = input("Rol (admin/user) [user]: ").strip().lower() or "user"
        if rol not in ("admin", "user"):
            rol = "user"
        password_hash_b64 = hash_password(password)
        try:
            cursor = self.mysql.cursor()
            cursor.execute(
                "INSERT INTO usuarios (username, email, password_hash, rol, activo) VALUES (%s, %s, %s, %s, %s)",
                (username, email, password_hash_b64, rol, True)
            )
            self.mysql.commit()
            last_id = cursor.lastrowid
            cursor.close()
        except:
            self.mysql.rollback()
            return
        self.mongo_users.insert_one({
            "mysql_id": last_id,
            "username": username,
            "email": email,
            "password_hash": password_hash_b64,
            "activo": True,
            "rol": rol,
            "created_at": datetime.now(UTC)
        })
        print("Usuario registrado correctamente.")
        self.crear_log(username, "registro")

    def login(self):
        self.asegurar_conexion_mysql()
        print("\n--- Login ---")
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")
        cursor = self.mysql.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        if not user:
            print("Usuario no encontrado.")
            self.crear_log(username, "login_fallido_no_usuario")
            return
        if not verify_password(password, user["password_hash"]):
            print("Contraseña incorrecta.")
            self.crear_log(username, "login_fallido_password")
            return
        if not user.get("activo", True):
            print("Cuenta inactiva.")
            return
        self.usuario_actual = user
        print(f"\n✔ Login exitoso. Bienvenido {user['username']} (rol: {user['rol']})")
        self.crear_log(user["username"], "login_exitoso")
        self.menu_post_login()

    def recuperar_contrasena(self):
        self.asegurar_conexion_mysql()
        print("\n--- Recuperación de contraseña (simulada) ---")
        email = input("Ingresa tu email: ").strip()
        cursor = self.mysql.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        if not user:
            print("No hay usuario con ese email.")
            return
        temp = secrets.token_urlsafe(8)
        print(f"(SIMULADO) Contraseña temporal: {temp}")
        new_hash = hash_password(temp)
        cursor = self.mysql.cursor()
        cursor.execute("UPDATE usuarios SET password_hash = %s WHERE id = %s", (new_hash, user["id"]))
        self.mysql.commit()
        cursor.close()
        self.mongo_users.update_one({"mysql_id": user["id"]}, {"$set": {"password_hash": new_hash}})
        self.crear_log(user["username"], "recuperacion_contrasena")
        print("Contraseña temporal aplicada.")

    def editar_mi_perfil(self):
        self.asegurar_conexion_mysql()
        if not self.usuario_actual:
            return
        uid = self.usuario_actual["id"]
        print("\n--- Editar perfil ---")
        print("1. Cambiar email")
        print("2. Cambiar username")
        print("3. Cambiar contraseña")
        print("4. Activar/Desactivar cuenta")
        print("0. Volver")
        opt = input("Opción: ")
        if opt == "1":
            nuevo = input("Nuevo email: ").strip()
            cursor = self.mysql.cursor()
            cursor.execute("UPDATE usuarios SET email=%s WHERE id=%s", (nuevo, uid))
            self.mysql.commit()
            cursor.close()
            self.mongo_users.update_one({"mysql_id": uid}, {"$set": {"email": nuevo}})
            self.usuario_actual["email"] = nuevo
            self.crear_log(self.usuario_actual["username"], "editar_email")
            print("Email actualizado.")
        elif opt == "2":
            nuevo = input("Nuevo username: ").strip()
            cursor = self.mysql.cursor(dictionary=True)
            cursor.execute("SELECT id FROM usuarios WHERE username = %s AND id != %s", (nuevo, uid))
            if cursor.fetchone():
                print("Username ya existe.")
                cursor.close()
                return
            cursor.close()
            cursor = self.mysql.cursor()
            cursor.execute("UPDATE usuarios SET username=%s WHERE id=%s", (nuevo, uid))
            self.mysql.commit()
            cursor.close()
            self.mongo_users.update_one({"mysql_id": uid}, {"$set": {"username": nuevo}})
            self.usuario_actual["username"] = nuevo
            self.crear_log(nuevo, "editar_username")
            print("Username actualizado.")
        elif opt == "3":
            pwd = getpass.getpass("Nueva contraseña: ")
            new_hash = hash_password(pwd)
            cursor = self.mysql.cursor()
            cursor.execute("UPDATE usuarios SET password_hash=%s WHERE id=%s", (new_hash, uid))
            self.mysql.commit()
            cursor.close()
            self.mongo_users.update_one({"mysql_id": uid}, {"$set": {"password_hash": new_hash}})
            self.crear_log(self.usuario_actual["username"], "cambio_contrasena")
            print("Contraseña actualizada.")
        elif opt == "4":
            nuevo_estado = not bool(self.usuario_actual.get("activo", True))
            cursor = self.mysql.cursor()
            cursor.execute("UPDATE usuarios SET activo=%s WHERE id=%s", (nuevo_estado, uid))
            self.mysql.commit()
            cursor.close()
            self.mongo_users.update_one({"mysql_id": uid}, {"$set": {"activo": nuevo_estado}})
            self.usuario_actual["activo"] = nuevo_estado
            self.crear_log(self.usuario_actual["username"], "cambio_estado")
            print("Estado cambiado.")

    def es_admin(self):
        return self.usuario_actual and self.usuario_actual.get("rol") == "admin"

    def ver_todos_usuarios(self):
        self.asegurar_conexion_mysql()
        cursor = self.mysql.cursor(dictionary=True)
        cursor.execute("SELECT id, username, email, rol, activo, fecha_registro FROM usuarios")
        for r in cursor.fetchall():
            print(r)
        cursor.close()

    def ver_logs(self, limit=50):
        for doc in self.mongo_logs.find().sort("fecha", -1).limit(limit):
            print({"usuario": doc.get("usuario"), "accion": doc.get("accion"), "fecha": doc.get("fecha"), "ip": doc.get("ip")})

    def eliminar_usuario(self):
        self.asegurar_conexion_mysql()
        uid = input("ID a eliminar: ").strip()
        if not uid.isdigit():
            print("ID inválido.")
            return
        uid = int(uid)
        cursor = self.mysql.cursor()
        cursor.execute("DELETE FROM usuarios WHERE id=%s", (uid,))
        self.mysql.commit()
        cursor.close()
        self.mongo_users.delete_many({"mysql_id": uid})
        self.crear_log(uid, "eliminar_usuario")
        print("Usuario eliminado.")

    def editar_usuario_admin(self):
        self.asegurar_conexion_mysql()
        uid = input("ID a editar: ").strip()
        if not uid.isdigit():
            print("ID inválido.")
            return
        uid = int(uid)
        cursor = self.mysql.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (uid,))
        user = cursor.fetchone()
        cursor.close()
        if not user:
            print("No existe.")
            return
        print(user)
        print("1. Cambiar rol")
        print("2. Cambiar email")
        print("3. Forzar contraseña temporal")
        opt = input("Opción: ")
        if opt == "1":
            nuevo = input("Nuevo rol (admin/user): ").strip()
            cursor = self.mysql.cursor()
            cursor.execute("UPDATE usuarios SET rol=%s WHERE id=%s", (nuevo, uid))
            self.mysql.commit()
            cursor.close()
            self.mongo_users.update_one({"mysql_id": uid}, {"$set": {"rol": nuevo}})
            self.crear_log(user["username"], "admin_cambio_rol")
            print("Rol actualizado.")
        elif opt == "2":
            nuevo = input("Nuevo email: ").strip()
            cursor = self.mysql.cursor()
            cursor.execute("UPDATE usuarios SET email=%s WHERE id=%s", (nuevo, uid))
            self.mysql.commit()
            cursor.close()
            self.mongo_users.update_one({"mysql_id": uid}, {"$set": {"email": nuevo}})
            self.crear_log(user["username"], "admin_cambio_email")
            print("Email actualizado.")
        elif opt == "3":
            temp = secrets.token_urlsafe(8)
            print(f"Temporal: {temp}")
            new_hash = hash_password(temp)
            cursor = self.mysql.cursor()
            cursor.execute("UPDATE usuarios SET password_hash=%s WHERE id=%s", (new_hash, uid))
            self.mysql.commit()
            cursor.close()
            self.mongo_users.update_one({"mysql_id": uid}, {"$set": {"password_hash": new_hash}})
            self.crear_log(user["username"], "admin_forzar_password")
            print("Contraseña temporal aplicada.")

    def menu_post_login(self):
        while self.usuario_actual:
            print("\n--- MENÚ POST LOGIN ---")
            print("1. Ver perfil")
            print("2. Editar mi perfil")
            print("3. Cerrar sesión")
            if self.es_admin():
                print("4. Ver usuarios")
                print("5. Ver logs")
                print("6. Editar usuario")
                print("7. Eliminar usuario")
            opt = input("Opción: ").strip()
            if opt == "1":
                print(self.usuario_actual)
            elif opt == "2":
                self.editar_mi_perfil()
            elif opt == "3":
                print("Cerrando sesión...")
                self.crear_log(self.usuario_actual["username"], "logout")
                self.usuario_actual = None
                break
            elif opt == "4" and self.es_admin():
                self.ver_todos_usuarios()
            elif opt == "5" and self.es_admin():
                self.ver_logs()
            elif opt == "6" and self.es_admin():
                self.editar_usuario_admin()
            elif opt == "7" and self.es_admin():
                self.eliminar_usuario()
            else:
                print("Opción inválida.")

    def main(self):
        while True:
            print("\n--- SISTEMA DE AUTENTICACIÓN ---")
            print("1. Registrar usuario")
            print("2. Login")
            print("3. Recuperar contraseña (simulada)")
            print("4. Salir")
            opt = input("Opción: ").strip()
            if opt == "1":
                self.registrar_usuario()
            elif opt == "2":
                self.login()
            elif opt == "3":
                self.recuperar_contrasena()
            elif opt == "4":
                print("Saliendo...")
                break
            else:
                print("Opción inválida.")

if __name__ == "__main__":
    SistemaAutenticacion().main()
