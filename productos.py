
import customtkinter as ctk
from tkinter import messagebox
from tkinter import ttk
from decimal import Decimal, InvalidOperation
import oracledb

from conexion import conectar


def crear_pestana_productos(pestana):

    titulo = ctk.CTkLabel(
        pestana,
        text="GESTION DE PRODUCTOS",
        font=("Arial", 22, "bold")
    )
    titulo.pack(pady=10)

    # Busqueda por ID
    buscador = ctk.CTkFrame(pestana)
    buscador.pack(fill="x", padx=20, pady=5)

    ctk.CTkLabel(
        buscador,
        text="ID del producto:"
    ).pack(side="left", padx=10)

    #Busqueda del ID de un producto
    entrada_id = ctk.CTkEntry(
        buscador,
        width=120,
        placeholder_text="Ej. 3"
    )
    entrada_id.pack(side="left", padx=5)

    id_seleccionado = None

    formulario = ctk.CTkScrollableFrame(
        pestana,
        height=300
    )
    formulario.pack(fill="x", padx=20, pady=10)

    # Campos con sus tipos de datos
    campos = [
        ("Codigo [TEXTO, max. 20]", "CODIGO"),
        ("Nombre [TEXTO, max. 100]", "NOMBRE"),
        ("Descripcion [TEXTO, max. 250]", "DESCRIPCION"),
        ("Categoria [TEXTO, max. 50]", "CATEGORIA"),
        ("Precio Compra [DECIMAL 10,2]", "PRECIO_COMPRA"),
        ("Precio Venta [DECIMAL 10,2]", "PRECIO_VENTA"),
        ("Impuesto [DECIMAL 5,2]", "IMPUESTO"),
        ("Stock [ENTERO]", "STOCK"),
        ("Stock Minimo [ENTERO]", "STOCK_MINIMO"),
        ("Stock Maximo [ENTERO]", "STOCK_MAXIMO"),
        ("ID Proveedor [ENTERO - FK]", "ID_PROVEEDOR_P")
    ]

    entradas = {}

    for i, (etiqueta, columna) in enumerate(campos):
        fila = i // 2
        lado = (i % 2) * 2

        ctk.CTkLabel(
            formulario,
            text=etiqueta
        ).grid(row=fila, column=lado, padx=10, pady=8)

        entrada = ctk.CTkEntry(
            formulario,
            width=200
        )
        entrada.grid(
            row=fila,
            column=lado + 1,
            padx=10,
            pady=8
        )

        entradas[columna] = entrada

    # Tabla visual de productos
    marco_tabla = ctk.CTkFrame(pestana)
    marco_tabla.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=10
    )

    columnas_tabla = (
        "ID", "CODIGO", "NOMBRE",
        "PRECIO", "STOCK", "PROVEEDOR"
    )

    tabla = ttk.Treeview(
        marco_tabla,
        columns=columnas_tabla,
        show="headings",
        height=8
    )

    for columna in columnas_tabla:
        tabla.heading(columna, text=columna)
        tabla.column(columna, width=120, anchor="center")

    tabla.column("ID", width=60)
    tabla.column("NOMBRE", width=200)

    barra_vertical = ttk.Scrollbar(
        marco_tabla,
        orient="vertical",
        command=tabla.yview
    )

    barra_horizontal = ttk.Scrollbar(
        marco_tabla,
        orient="horizontal",
        command=tabla.xview
    )

    tabla.configure(
        yscrollcommand=barra_vertical.set,
        xscrollcommand=barra_horizontal.set
    )

    marco_tabla.grid_rowconfigure(0, weight=1)
    marco_tabla.grid_columnconfigure(0, weight=1)

    tabla.grid(
        row=0, column=0,
        sticky="nsew"
    )

    barra_vertical.grid(
        row=0, column=1,
        sticky="ns"
    )

    barra_horizontal.grid(
        row=1, column=0,
        sticky="ew"
    )

    def consultar_productos():
        try:
            with conectar() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute("""
                        SELECT ID_PRODUCTO_P,
                               CODIGO,
                               NOMBRE,
                               PRECIO_VENTA,
                               STOCK,
                               ID_PROVEEDOR_P
                        FROM PRODUCTOS_P
                        ORDER BY ID_PRODUCTO_P
                    """)

                    registros = cursor.fetchall()

            # Limpiar las filas anteriores de la tabla
            for item in tabla.get_children():
                tabla.delete(item)

            # Mostrar los productos consultados
            for registro in registros:
                tabla.insert(
                    "",
                    "end",
                    values=[
                        "" if dato is None else str(dato)
                        for dato in registro
                    ]
                )

        except (oracledb.Error, ValueError) as error:
            messagebox.showerror(
                "Error de consulta",
                str(error)
            )

    def buscar_producto():
        nonlocal id_seleccionado

        texto_id = entrada_id.get().strip()

        if not texto_id.isdecimal() or int(texto_id) <= 0:
            messagebox.showwarning(
                "Validacion",
                "Introduce un ID entero positivo."
            )
            return

        id_producto = int(texto_id)
        id_seleccionado = None

        try:
            with conectar() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute("""
                        SELECT CODIGO, NOMBRE, DESCRIPCION,
                               CATEGORIA, PRECIO_COMPRA,
                               PRECIO_VENTA, IMPUESTO,
                               STOCK, STOCK_MINIMO,
                               STOCK_MAXIMO, ID_PROVEEDOR_P
                        FROM PRODUCTOS_P
                        WHERE ID_PRODUCTO_P = :id
                    """, {"id": id_producto})

                    producto = cursor.fetchone()

            if producto is None:
                messagebox.showinfo(
                    "Busqueda",
                    "No existe un producto con ese ID."
                )
                return

            columnas = [
                "CODIGO", "NOMBRE", "DESCRIPCION",
                "CATEGORIA", "PRECIO_COMPRA",
                "PRECIO_VENTA", "IMPUESTO",
                "STOCK", "STOCK_MINIMO",
                "STOCK_MAXIMO", "ID_PROVEEDOR_P"
            ]

            for columna, valor in zip(columnas, producto):
                entradas[columna].delete(0, "end")
                entradas[columna].insert(
                    0,
                    "" if valor is None else str(valor)
                )

            id_seleccionado = id_producto

            # Mostrar solamente el producto buscado en la tabla
            for item in tabla.get_children():
                tabla.delete(item)

            tabla.insert(
                "",
                "end",
                values=(
                    id_producto,
                    producto[0],   # CODIGO
                    producto[1],   # NOMBRE
                    producto[5],   # PRECIO_VENTA
                    producto[7],   # STOCK
                    producto[10]   # ID_PROVEEDOR_P
                )
            )

            messagebox.showinfo(
                "Busqueda",
                "Producto cargado en el formulario."
            )

        except oracledb.Error as error:
            messagebox.showerror(
                "Error de Oracle",
                str(error)
            )

    def obtener_datos():
        nombre = entradas["NOMBRE"].get().strip()
        proveedor_texto = entradas["ID_PROVEEDOR_P"].get().strip()

        if not nombre:
            raise ValueError("El nombre es obligatorio.")

        if not proveedor_texto.isdecimal():
            raise ValueError(
                "El proveedor debe ser un ID entero positivo."
            )

        proveedor = int(proveedor_texto)

        if proveedor <= 0:
            raise ValueError(
                "El proveedor debe ser positivo."
            )

        def decimal_opcional(campo):
            texto = entradas[campo].get().strip()

            if not texto:
                return None

            numero = Decimal(texto)

            if not numero.is_finite() or numero < 0:
                raise ValueError(
                    f"{campo} debe ser un decimal no negativo."
                )

            return numero

        def entero_opcional(campo):
            texto = entradas[campo].get().strip()

            if not texto:
                return None

            if not texto.isdecimal():
                raise ValueError(
                    f"{campo} debe ser un entero no negativo."
                )

            return int(texto)

        datos = {
            "codigo": entradas["CODIGO"].get().strip() or None,
            "nombre": nombre,
            "descripcion": entradas["DESCRIPCION"].get().strip() or None,
            "categoria": entradas["CATEGORIA"].get().strip() or None,
            "precio_compra": decimal_opcional("PRECIO_COMPRA"),
            "precio_venta": decimal_opcional("PRECIO_VENTA"),
            "impuesto": decimal_opcional("IMPUESTO"),
            "stock": entero_opcional("STOCK"),
            "stock_minimo": entero_opcional("STOCK_MINIMO"),
            "stock_maximo": entero_opcional("STOCK_MAXIMO"),
            "proveedor": proveedor
        }

        minimo = datos["stock_minimo"]
        maximo = datos["stock_maximo"]

        if minimo is not None and maximo is not None:
            if minimo > maximo:
                raise ValueError(
                    "Stock minimo no puede superar al maximo."
                )

        return datos

    def guardar_producto():
        try:
            nombre = entradas["NOMBRE"].get().strip()

            if not nombre:
                messagebox.showwarning(
                    "Validacion",
                    "El nombre es obligatorio."
                )
                return

            proveedor_texto = entradas[
                "ID_PROVEEDOR_P"
            ].get().strip()

            if not proveedor_texto:
                messagebox.showwarning(
                    "Validacion",
                    "El proveedor es obligatorio."
                )
                return

            proveedor = int(proveedor_texto)

            if proveedor <= 0:
                raise ValueError(
                    "El ID del proveedor debe ser positivo."
                )

            def numero_decimal(campo):
                valor = entradas[campo].get().strip()

                if not valor:
                    return None

                numero = Decimal(valor)

                if not numero.is_finite():
                    raise ValueError("Numero no valido.")

                return numero

            def numero_entero(campo):
                valor = entradas[campo].get().strip()
                return int(valor) if valor else None

            datos = {
                "codigo": entradas["CODIGO"].get().strip() or None,
                "nombre": nombre,
                "descripcion": entradas["DESCRIPCION"].get().strip() or None,
                "categoria": entradas["CATEGORIA"].get().strip() or None,
                "precio_compra": numero_decimal("PRECIO_COMPRA"),
                "precio_venta": numero_decimal("PRECIO_VENTA"),
                "impuesto": numero_decimal("IMPUESTO"),
                "stock": numero_entero("STOCK"),
                "stock_minimo": numero_entero("STOCK_MINIMO"),
                "stock_maximo": numero_entero("STOCK_MAXIMO"),
                "proveedor": proveedor
            }

            # Validar valores negativos
            for campo in (
                "precio_compra",
                "precio_venta",
                "impuesto",
                "stock",
                "stock_minimo",
                "stock_maximo"
            ):
                valor = datos[campo]

                if valor is not None and valor < 0:
                    raise ValueError(
                        f"{campo} no puede ser negativo."
                    )

            # Validar limites de stock
            if (
                datos["stock_minimo"] is not None
                and datos["stock_maximo"] is not None
                and datos["stock_minimo"] > datos["stock_maximo"]
            ):
                raise ValueError(
                    "Stock minimo supera al maximo."
                )

            # Insertar en Oracle
            with conectar() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO PRODUCTOS_P (
                            CODIGO,
                            NOMBRE,
                            DESCRIPCION,
                            CATEGORIA,
                            PRECIO_COMPRA,
                            PRECIO_VENTA,
                            IMPUESTO,
                            STOCK,
                            STOCK_MINIMO,
                            STOCK_MAXIMO,
                            ID_PROVEEDOR_P
                        ) VALUES (
                            :codigo,
                            :nombre,
                            :descripcion,
                            :categoria,
                            :precio_compra,
                            :precio_venta,
                            :impuesto,
                            :stock,
                            :stock_minimo,
                            :stock_maximo,
                            :proveedor
                        )
                    """, datos)

                    conexion.commit()

            messagebox.showinfo(
                "Exito",
                "Producto guardado correctamente."
            )

            # Limpiar formulario
            for entrada in entradas.values():
                entrada.delete(0, "end")

            # Actualizar listado
            consultar_productos()

        except (ValueError, InvalidOperation) as error:
            messagebox.showerror(
                "Datos incorrectos",
                str(error)
            )

        except oracledb.Error as error:
            messagebox.showerror(
                "Error de Oracle",
                str(error)
            )

    def actualizar_producto():
        if id_seleccionado is None:
            messagebox.showwarning(
                "Actualizar",
                "Primero busca un producto por ID."
            )
            return

        try:
            datos = obtener_datos()
            datos["id_producto"] = id_seleccionado

            with conectar() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute("""
                        UPDATE PRODUCTOS_P
                        SET CODIGO = :codigo,
                            NOMBRE = :nombre,
                            DESCRIPCION = :descripcion,
                            CATEGORIA = :categoria,
                            PRECIO_COMPRA = :precio_compra,
                            PRECIO_VENTA = :precio_venta,
                            IMPUESTO = :impuesto,
                            STOCK = :stock,
                            STOCK_MINIMO = :stock_minimo,
                            STOCK_MAXIMO = :stock_maximo,
                            ID_PROVEEDOR_P = :proveedor
                        WHERE ID_PRODUCTO_P = :id_producto
                    """, datos)

                    modificados = cursor.rowcount

                    if modificados == 1:
                        conexion.commit()

            if modificados == 0:
                messagebox.showwarning(
                    "Actualizar",
                    "El producto ya no existe."
                )
                return

            messagebox.showinfo(
                "Exito",
                "Producto actualizado correctamente."
            )

            consultar_productos()

        except (ValueError, InvalidOperation) as error:
            messagebox.showerror(
                "Datos incorrectos",
                str(error)
            )

        except oracledb.Error as error:
            messagebox.showerror(
                "Error de Oracle",
                str(error)
            )

    def eliminar_producto():
        nonlocal id_seleccionado

        if id_seleccionado is None:
            messagebox.showwarning(
                "Eliminar",
                "Primero busca un producto por ID."
            )
            return

        confirmar = messagebox.askyesno(
            "Confirmar eliminacion",
            f"¿Deseas eliminar el producto ID {id_seleccionado}?"
        )

        if not confirmar:
            return

        try:
            with conectar() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute("""
                        DELETE FROM PRODUCTOS_P
                        WHERE ID_PRODUCTO_P = :id
                    """, {"id": id_seleccionado})

                    eliminados = cursor.rowcount

                    if eliminados == 1:
                        conexion.commit()

            if eliminados == 0:
                messagebox.showwarning(
                    "Eliminar",
                    "El producto ya no existe."
                )
                return

            messagebox.showinfo(
                "Exito",
                "Producto eliminado correctamente."
            )

            id_seleccionado = None
            entrada_id.delete(0, "end")

            for entrada in entradas.values():
                entrada.delete(0, "end")

            consultar_productos()

        except oracledb.Error as error:
            messagebox.showerror(
                "Error de Oracle",
                str(error)
            )

    # Botones
    botones = ctk.CTkFrame(pestana)
    botones.pack(pady=5)

    ctk.CTkButton(
        botones,
        text="Guardar producto",
        command=guardar_producto
    ).pack(side="left", padx=10)

    ctk.CTkButton(
        botones,
        text="Consultar productos",
        command=consultar_productos
    ).pack(side="left", padx=10)

    ctk.CTkButton(
        buscador,
        text="Buscar ID",
        command=buscar_producto,
        width=100
    ).pack(side="left", padx=10)

    ctk.CTkButton(
        botones,
        text="Actualizar",
        command=actualizar_producto
    ).pack(side="left", padx=10)

    ctk.CTkButton(
        botones,
        text="Eliminar",
        command=eliminar_producto,
        fg_color="#B83B3B",
        hover_color="#922D2D"
    ).pack(side="left", padx=10)

    # Mostrar registros al iniciar
    consultar_productos()
