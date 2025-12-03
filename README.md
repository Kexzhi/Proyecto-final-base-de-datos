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
  
+Decisiones Propio:
  