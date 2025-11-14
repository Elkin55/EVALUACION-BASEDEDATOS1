# 🟦 Sistema de Autenticación con MySQL + MongoDB (Python)

Proyecto en Python que implementa un sistema de autenticación con **registro**, **login**, **roles**, **recuperación simulada de contraseña**, **edición de perfil** y **registro de actividades** usando MySQL y MongoDB.

---

## 🚀 Tecnologías

* Python 3
* MySQL (Clever Cloud)
* MongoDB Atlas
* bcrypt
* mysql-connector-python
* pymongo

---

## 📌 Funcionalidades

✔ Registrar usuarios
✔ Roles: **admin** y **user**
✔ Login
✔ Recuperar contraseña (simulada)
✔ Editar email / contraseña
✔ Logs de login en MongoDB
✔ Hash seguro de contraseñas

---

## 📂 Estructura

```
main.py
requirements.txt
.env          # variables de entorno
.gitignore
README.md
```

---

## ⚙️ Configuración

### 1️⃣ Archivo `.env`

```
MYSQL_HOST=...
MYSQL_USER=...
MYSQL_PASSWORD=...
MYSQL_DATABASE=...
MYSQL_PORT=3306
MONGO_URI=mongodb+srv://...
```

### 2️⃣ Tabla MySQL

```sql
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol ENUM('admin','user') DEFAULT 'user',
    created_at DATETIME
);
```

---

## ▶️ Ejecución

```
pip install -r requirements.txt
python main.py
```

---

## ✔ Pruebas

* Registrar usuario
* Iniciar sesión y revisar logs en MongoDB
* Recuperar contraseña
* Editar perfil
* Probar cuentas admin y user

---

## 👨‍💻 Autor

**Elkin Renan Saltos Macías**
Materia: Interacción Humano Computador
Docente: Ing. Gómez Bravo Josselyn Tatiana

