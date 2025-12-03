# Sistemas de Inventario Unison
#### Aplicacion de escritorio hecha con phyton, SQLite y control de roles.
<img src="./IMAGENES GITHUB/LOGO-OJO-BUHO-NEGRO-2048x1669.jpg" width="430">

## Info de proyecto
 - **Lenguaje: Python**

 - **Tipo: Desktop App**

 - **Estado: Finalizado**

### ¿Para que nos sirve este proyecto?
- basicamente es un proyecto diseñando para gente que no sabe mucho sobre base de datos
- Programa para modificar base de datos y protegerla con su inicio de sesion
- Borrar ,Editar y Agregar  

# contenido:
- [INTRODUCCIÓN](#descripcion-general)
- [SOLUCION](#vista-pajaro)
- [TECNOLOGIAS](#Arquitectura-tecnica)
- [SEGURIDAD](#base-de-datos-y-su-seguridad)
- [VISTA](#Funcionalidad-por-vista)
- [IA](#USO-DE-IA-EN-EL-DESAROLLO)
- [COMO HACER EL PROYECTO EJECJUTABLE](#pasos-y-algunos-tips)
- [DESAFIOS](#RETOS-Y-SOLUCION)
- [CONCLUSION](#LO-QUE-APRENDI-MIENTRAS-HACIA-TODO-EL-PROYECTO)

# INTRUDUCCIÓN

En esta pratica basicamente nos dieron la oportunidad de elegir el lenguaje de programacion que queramos elegi python para hacer este sistema basico de inventario por su facilidad de aprender y baja complejidad al encontrar informacion acerca de este lenguaje, basicamente la aplicacion es una interfaz para que el usuario que no sepa utilizar base de datos pueda alterar la base de datos , dependiendo de su rol y su tipo de usuario teniendo la posibilidad de alterarla sin saber nada sobre base de datos , desde agregar un nuevo producto o almacen, hasta modificarla, y eliminarlos. Tambien tiene la posibilidad de encontrar la informacion filtrando la informacion, para terminar pues la base de datos estara mas protegida porque ocuparas hacer login, todo esto se guardara en su propia base da datos pero la contraseña no sera un texto plano, estara encriptada asi que no cualquier podra acceder, tambien tiene distintos roles en donde cada uno solo podra hacer cierta cosas para evitar el problema de que cualquiera pueda modificar , eliminar y hacer lo que quiera con la base de datos. 

### ¿Qué problema resuelve?

- Inventario pequeño, control de productos y almacenes.
- Necesidad de saber qué se mueve y quien lo modifica.
- Tener que saber alguna forma de modificar base de datos
- Automatizacion de procesos 
- Mayor control en el inventario

### ¿En qué contexto se hizo?
- Se hizo para el final de semestre como proyecto final

### Restricciones para el proyecto
- Contraseña encriptada 
- una solo ventana, no ventanas emergente 
- informacion "Sensible". asi que se requiere login y roles.

# SOLUCION

La solución al problema que nos dio el profesor basicamente crear una aplicación que pudiera leer la base de datos ,con su propio inicio de secion seguro , contraseña cifrada para mas seguridad , lo roles con su permisos ,filtros , auditioria automatica , intento de inferzar moderna y su propio .exe

+ Tipo de solucion:
  - [Aplicación](dist/InventarioUNISON.exe)
  
+ Arquitectura general del proyecto:
  - Capa de interfaz [UI_WIDGETS.PY](ui_widgets.py) y [VIEW_*.PY](views_usuarios.py)
  - Capa Logica [Main](main.py)
  - capa de datos [DB_UTILS.py](db_utils.py) y [DB](InventarioBD_2.db)

+ Decisiones Propias:
    - No ventanas , Todo en una misma ventana
    - Vista usuario , modificar usuarios , roles y crear nuevo usuarios
    - Buen diseño

# TECNOLOGIA

Para este proyecto usé tecnologías sencillas pero muy útiles para alguien que va empezando:

- **Lenguaje:** Python 3.x
- **Interfaz gráfica:**
    - `tkinter`
    - `customtkinter` para darle un estilo más moderno (dark mode, botones bonitos, etc.)
- **Base de datos:** `SQLite` (módulo `sqlite3` de Python)
- **Encriptación de contraseñas:** `hashlib` (SHA-256 + salt)
- **Empaquetado a .exe:** `PyInstaller` usando el archivo `InventarioUNISON.spec`

### Estructura de carpetas y archivos principales

- `main.py` → punto de entrada de la aplicación.
- `settings.py` → configuración general (ruta de la BD, nombres de roles, etc.).
- `db_utils.py` → toda la lógica de base de datos:
    - conexión a SQLite
    - creación de tablas
    - manejo de usuarios y almacenes
    - autenticación y auditoría
- `ui_widgets.py` → componentes visuales reutilizables (inputs, botones, contenedores).
- `views_login.py` → pantalla de inicio de sesión.
- `views_productos.py` → vista para manejar productos.
- `views_almacenes.py` → vista para manejar almacenes.
- `views_usuarios.py` → vista para manejar usuarios y roles.
- `InventarioBD_2.db` → archivo físico de la base de datos.
- `InventarioUNISON.spec` → archivo de configuración para generar el `.exe`.

Con esto se logra separar bien la lógica de datos, la interfaz y la configuración, para que el código sea más fácil de mantener y entender.

---

# BASE DE DATOS Y SU SEGURIDAD

La base de datos es un archivo `SQLite` (`InventarioBD_2.db`), ideal para proyectos pequeños/medianos porque no requiere servidor externo.

### Tablas principales

- **usuarios**
    - `id` (PK, autoincremental)
    - `nombre` (único)
    - `password_hash`
    - `salt`
    - `fecha_hora_ultimo_inicio`
    - `rol` (`ADMIN`, `PRODUCTOS`, `ALMACENES`, `VISITANTE`)

- **almacenes**
    - `id` (PK)
    - `nombre`
    - `fecha_hora_creacion`
    - `fecha_hora_ultima_modificacion`
    - `ultimo_usuario_en_modificar`

- **productos** (estructura básica, puede variar)
    - `id` (PK)
    - `nombre`
    - `cantidad`
    - `almacen_id` (FK a `almacenes`)
    - columnas de auditoría similares (quién y cuándo modificó)

### Seguridad de contraseñas

Las contraseñas **no se guardan en texto plano**:

1. Cuando se registra o actualiza un usuario, se genera un `salt` aleatorio.
2. Se calcula un `hash` con `SHA-256` usando ese `salt` + contraseña.
3. En la BD solo se almacena:
    - `salt`
    - `password_hash`
4. En el login, se vuelve a calcular el hash y se compara.

Así, aunque alguien abra el archivo `.db`, no puede ver las contraseñas reales.

### Control de roles

Los roles están definidos en `settings.py`:

- `ADMIN`
- `PRODUCTOS`
- `ALMACENES`
- `VISITANTE`

Cada uno tiene distintos permisos dentro de la interfaz. De esta forma, no cualquiera puede borrar o modificar todo.

---

# Funcionalidad por vista

Aquí explico qué hace cada pantalla principal.

### 1. Login (`views_login.py`)

- Pantalla inicial de la app.
- Campos:
    - Usuario
    - Contraseña
- El login es **sensible a mayúsculas/minúsculas**:
    - Si en la BD el usuario es `ADMIN`, no funciona `admin`.
- Al iniciar sesión:
    - Se valida usuario y contraseña.
    - Se actualiza `fecha_hora_ultimo_inicio` en la BD.
    - Se abre la ventana principal con el rol adecuado.

### 2. Vista principal / navegación

- Una sola ventana para todo (por restricción del proyecto).
- Desde aquí se puede cambiar de módulo:
    - Productos
    - Almacenes
    - Usuarios (solo admin)
- Cada cambio de sección reutiliza el mismo contenedor, no se abren ventanas nuevas.

### 3. Vista de Productos (`views_productos.py`)

- Listado de productos con tabla.
- Funciones principales:
    - Agregar producto
    - Editar producto
    - Eliminar producto
    - Filtrar por nombre / almacén, etc.
- Cada operación impacta directamente en la BD.
- Opcionalmente se muestran columnas de auditoría (quién y cuándo modificó por última vez).

### 4. Vista de Almacenes (`views_almacenes.py`)

- Lista todos los almacenes registrados.
- Acciones:
    - Crear nuevo almacén
    - Renombrar almacén
    - Eliminar almacén
- Incluye:
    - `fecha_hora_creacion`
    - `fecha_hora_ultima_modificacion`
    - `ultimo_usuario_en_modificar`

### 5. Vista de Usuarios (`views_usuarios.py`)

- Disponible solo para el rol `ADMIN`.
- Permite:
    - Crear usuarios nuevos con rol asignado.
    - Cambiar contraseña.
    - Cambiar rol.
    - Eliminar usuarios.
- Sirve para administrar quién puede entrar al sistema y qué puede hacer.

---

# USO DE IA EN EL DESAROLLO

Durante el desarrollo utilicé herramientas de IA (como ChatGPT) para:

- Diseñar y corregir la estructura de la base de datos.
- Implementar el sistema de:
    - Hash de contraseñas con `salt`.
    - Auditoría automática de cambios.
- Resolver errores de imports, rutas y nombres de funciones.
- Mejorar la organización del proyecto en capas:
    - interfaz (`views_*.py`, `ui_widgets.py`)
    - lógica (`main.py`)
    - datos (`db_utils.py`)
- Redactar y pulir este README y algunos comentarios en el código.

La IA se usó como apoyo, pero todas las pruebas, decisiones finales y ajustes se hicieron manualmente para asegurar que el proyecto cumpla con las restricciones de la materia.

---

# PASOS Y ALGUNOS TIPS

### Requisitos previos

- Python 3.x instalado.
- Paquetes necesarios:
    - `customtkinter`
    - (opcional) cualquier otro módulo extra que uses en el proyecto.

Puedes instalarlos con:

```bash
pip install customtkinter

