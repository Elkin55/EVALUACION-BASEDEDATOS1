# Sistema de Autenticación con MySQL y MongoDB

Este proyecto implementa un sistema de autenticación utilizando dos bases de datos:

* **MySQL (Clever Cloud)** para almacenar los usuarios principales
* **MongoDB Atlas** para almacenar los datos complementarios y los registros (logs)

El sistema incluye registro, login, edición de perfil, recuperación de contraseña (simulada) y manejo de roles (admin/usuario), además de almacenamiento de logs de acceso.

---

## 1. Requisitos

Antes de instalar el sistema, es necesario contar con:

* Python 3.10 o superior
* PIP instalado
* Git instalado
* Cuenta en MongoDB Atlas
* Cuenta en Clever Cloud (MySQL)

---

## 2. Instalación del proyecto

Clonar el repositorio:

```
git clone https://github.com/TU_USUARIO/TU_REPO.git
cd TU_REPO
```

Instalar dependencias:

```
pip install -r requirements.txt
```

Si no existe el archivo requirements.txt, instalar manualmente:

```
pip install pymongo mysql-connector-python bcrypt
```

---

## 3. Configuración de MongoDB Atlas

1. Crear un Cluster en MongoDB Atlas.
2. Ir a Network Access > Add IP Address.
3. Seleccionar la opción: Allow access from anywhere (0.0.0.0/0).
4. Crear un usuario en Database Access.
5. Copiar la cadena de conexión del cluster, por ejemplo:

```
mongodb+srv://USUARIO:CONTRASEÑA@CLUSTER.mongodb.net/?retryWrites=true&w=majority
```

6. Reemplazar en el archivo `main.py`:

```python
MONGO_URI = "TU_URI_AQUI"
```

---

## 4. Configuración de MySQL en Clever Cloud

1. Crear una base de datos MySQL en Clever Cloud.

2. Ir a Service/Environment variables.

3. Copiar los valores proporcionados por la plataforma:

   * MYSQL_ADDON_HOST
   * MYSQL_ADDON_DB
   * MYSQL_ADDON_USER
   * MYSQL_ADDON_PASSWORD
   * MYSQL_ADDON_PORT

4. Colocar los valores correspondientes en `main.py`:

```python
MYSQL_HOST = "..."
MYSQL_USER = "..."
MYSQL_PASSWORD = "..."
MYSQL_DATABASE = "..."
MYSQL_PORT = 3306
```

5. Crear la tabla necesaria ejecutando lo siguiente en MySQL:

```sql
CREATE TABLE usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) UNIQUE,
  email VARCHAR(100),
  password_hash VARCHAR(255),
  rol VARCHAR(20),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

---

## 5. Ejecución del sistema

Para iniciar la aplicación:

```
python main.py
```

Se mostrará el menú principal:

```
1. Registrar usuario
2. Login
3. Recuperar contraseña
4. Editar perfil
5. Salir
```

---

## 6. Pruebas recomendadas

* Registro de usuario y verificación en MySQL y MongoDB.
* Inicio de sesión con credenciales correctas e incorrectas.
* Verificación de roles (admin y usuario).
* Edición de perfil (email y contraseña).
* Verificación de logs almacenados en MongoDB en la colección correspondiente.

---

## Autor

Proyecto desarrollado por **Elkin Saltos**.
