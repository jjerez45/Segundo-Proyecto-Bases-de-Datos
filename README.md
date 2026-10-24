# Segundo-Proyecto-Bases-de-Datos
# Sistema Contable - Python y Oracle

## Descripción

Sistema Contable desarrollado en Python mediante una interfaz gráfica conectada a Oracle Database.

El proyecto permite administrar información mediante operaciones CRUD (crear, consultar, actualizar y eliminar registros).

La base de datos está compuesta por 12 tablas relacionadas, de las cuales se seleccionaron cinco para desarrollar la interfaz.

## Tecnologías utilizadas

- Python
- CustomTkinter
- Tkinter Treeview
- Oracle Database
- python-oracledb
- python-dotenv
- Visual Studio Code

## Módulos del sistema

- Productos
- Facturas de Venta
- Clientes
- Proveedores
- Cuentas Bancarias

Cada módulo permite registrar, consultar, buscar, actualizar y eliminar información.

## Instalación

Clonar o descargar el repositorio.

Instalar las dependencias necesarias:

```bash
pip install customtkinter oracledb python-dotenv
```

## Configuración de Oracle

Crear un archivo `.env` en la carpeta principal del proyecto con las siguientes variables:

```env
ORACLE_USER=usuario
ORACLE_PASSWORD=contraseña
ORACLE_HOST=servidor
ORACLE_PORT=1521
ORACLE_SID=identificador
```

Se requiere acceso autorizado a una base de datos Oracle que contenga las tablas del proyecto.

Por seguridad, el archivo `.env` no debe publicarse en GitHub.

## Ejecución

Desde la terminal, ejecutar:

```bash
python app.py
```

El programa abrirá la ventana principal del Sistema Contable con sus cinco módulos disponibles.

## Proyecto académico

Segundo proyecto en grupo del curso de Bases de Datos.

Universidad Mariano Gálvez de Guatemala.
