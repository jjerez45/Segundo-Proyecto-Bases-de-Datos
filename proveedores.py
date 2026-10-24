
import customtkinter as ctk
from tkinter import messagebox, ttk
import oracledb

from conexion import conectar


# MENSAJES DE ERROR DE ORACLE

def mensaje_error_oracle(error):
    detalle = error.args[0] if error.args else None
    codigo = getattr(detalle, "code", None)

    if codigo == 1:
        return "Ya existe un proveedor con ese codigo o NIT."

    if codigo == 2292:
        return (
            "No se puede eliminar: el proveedor tiene "
            "registros relacionados."
        )

    if codigo == 1400:
        return "Falta un campo obligatorio."

    if codigo == 12899:
        return "Uno de los textos supera la longitud permitida."

    return str(error)


def crear_pestana_proveedores(pestana):

    # 1. CONFIGURACION

    NOMBRE_TABLA = "PROVEEDORES_P"
    CLAVE_PRIMARIA = "ID_PROVEEDOR_P"

    campos = [
        ("Codigo proveedor", "CODIGO_PROVEEDOR"),
        ("NIT", "NIT"),
        ("Nombre", "NOMBRE"),
        ("Telefono", "TELEFONO"),
        ("Codigo postal", "CODIGO_POSTAL"),
        ("Direccion", "DIRECCION")
    ]

    longitudes = {
        "CODIGO_PROVEEDOR": 20,
        "NIT": 20,
        "NOMBRE": 100,
        "TELEFONO": 20,
        "CODIGO_POSTAL": 10,
        "DIRECCION": 150
    }

    columnas_tabla = (
        CLAVE_PRIMARIA,
        "CODIGO_PROVEEDOR",
        "NIT",
        "NOMBRE",
        "TELEFONO",
        "CODIGO_POSTAL",
        "DIRECCION"
    )

    anchos = {
        CLAVE_PRIMARIA: 110,
        "NOMBRE": 180,
        "DIRECCION": 220
    }

    id_seleccionado = None
    entradas = {}

    # 2. INTERFAZ

    ctk.CTkLabel(
        pestana,
        text="GESTION DE PROVEEDORES",
        font=("Arial", 22, "bold")
    ).pack(pady=10)

    buscador = ctk.CTkFrame(pestana)
    buscador.pack(fill="x", padx=20, pady=5)

    ctk.CTkLabel(
        buscador,
        text="ID del proveedor:"
    ).pack(side="left", padx=10)

    entrada_id = ctk.CTkEntry(
        buscador,
        width=120,
        placeholder_text="Ej. 1"
    )
    entrada_id.pack(side="left", padx=5)

    formulario = ctk.CTkScrollableFrame(
        pestana,
        height=150
    )
    formulario.pack(fill="x", padx=20, pady=10)

    for i, (etiqueta, columna) in enumerate(campos):
        fila = i // 2
        lado = (i % 2) * 2

        ctk.CTkLabel(
            formulario,
            text=etiqueta
        ).grid(
            row=fila,
            column=lado,
            padx=10,
            pady=8
        )

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

    # Reservamos espacio para los botones.
    botones = ctk.CTkFrame(pestana)
    botones.pack(side="bottom", pady=5)

    marco_tabla = ctk.CTkFrame(pestana)
    marco_tabla.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=10
    )

    tabla = ttk.Treeview(
        marco_tabla,
        columns=columnas_tabla,
        show="headings",
        height=8
    )

    for columna in columnas_tabla:
        tabla.heading(columna, text=columna)
        tabla.column(
            columna,
            width=anchos.get(columna, 130),
            anchor="center"
        )

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

    tabla.grid(row=0, column=0, sticky="nsew")
    barra_vertical.grid(row=0, column=1, sticky="ns")
    barra_horizontal.grid(row=1, column=0, sticky="ew")

    # 3. FUNCIONES AUXILIARES

    def limpiar_formulario():
        for entrada in entradas.values():
            entrada.delete(0, "end")

    def limpiar_seleccion():
        nonlocal id_seleccionado

        id_seleccionado = None
        entrada_id.delete(0, "end")
        limpiar_formulario()

    def obtener_datos():
        datos = {}

        for etiqueta, columna in campos:
            valor = entradas[columna].get().strip()
            datos[columna] = valor if valor else None

        # Campo obligatorio del codigo original
        if datos["NOMBRE"] is None:
            raise ValueError(
                "El nombre del proveedor es obligatorio."
            )

        # Validar longitudes en bytes
        for etiqueta, columna in campos:
            valor = datos[columna]

            if valor is not None:
                longitud = len(valor.encode("utf-8"))

                if longitud > longitudes[columna]:
                    raise ValueError(
                        f"{etiqueta}: maximo "
                        f"{longitudes[columna]} bytes."
                    )

        # Validar NIT
        if datos["NIT"] is not None:
            datos["NIT"] = datos["NIT"].upper()

            if not all(
                c.isdigit() or c in "-K"
                for c in datos["NIT"]
            ):
                raise ValueError(
                    "El NIT solo admite numeros, "
                    "guion y K. Ej. 1234567-8"
                )

        # Validar telefono
        if datos["TELEFONO"] is not None:
            if not all(
                c.isdigit() or c in " -+()"
                for c in datos["TELEFONO"]
            ):
                raise ValueError(
                    "El telefono contiene "
                    "caracteres no permitidos."
                )

        # Validar codigo postal
        if datos["CODIGO_POSTAL"] is not None:
            if not datos["CODIGO_POSTAL"].isdigit():
                raise ValueError(
                    "El codigo postal solo admite numeros."
                )

        return datos

    # 4. CONSULTAR

    def consultar_registros():
        try:
            with conectar() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute(f"""
                        SELECT {", ".join(columnas_tabla)}
                        FROM {NOMBRE_TABLA}
                        ORDER BY {CLAVE_PRIMARIA}
                    """)

                    registros = cursor.fetchall()

            for item in tabla.get_children():
                tabla.delete(item)

            for registro in registros:
                tabla.insert(
                    "",
                    "end",
                    values=[
                        "" if dato is None else str(dato)
                        for dato in registro
                    ]
                )

        except oracledb.Error as error:
            messagebox.showerror(
                "Error de consulta",
                mensaje_error_oracle(error)
            )

    # 5. BUSCAR POR ID

    def buscar_registro():
        nonlocal id_seleccionado

        texto_id = entrada_id.get().strip()

        if not texto_id.isdecimal() or int(texto_id) <= 0:
            messagebox.showwarning(
                "Validacion",
                "Introduce un ID entero positivo."
            )
            return

        id_buscado = int(texto_id)
        id_seleccionado = None

        columnas = [col for _, col in campos]

        try:
            with conectar() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute(f"""
                        SELECT {", ".join(columnas)}
                        FROM {NOMBRE_TABLA}
                        WHERE {CLAVE_PRIMARIA} = :id
                    """, {"id": id_buscado})

                    registro = cursor.fetchone()

            if registro is None:
                limpiar_formulario()
                messagebox.showinfo(
                    "Busqueda",
                    "No existe ese proveedor."
                )
                return

            for columna, valor in zip(columnas, registro):
                entradas[columna].delete(0, "end")
                entradas[columna].insert(
                    0,
                    "" if valor is None else str(valor)
                )

            id_seleccionado = id_buscado

            # Mostrar solamente el registro encontrado
            consultar_registros()

            for item in tabla.get_children():
                valores = tabla.item(item, "values")

                if str(valores[0]) != str(id_buscado):
                    tabla.delete(item)

            messagebox.showinfo(
                "Busqueda",
                "Proveedor cargado correctamente."
            )

        except oracledb.Error as error:
            messagebox.showerror(
                "Error de Oracle",
                mensaje_error_oracle(error)
            )

    # 6. INSERT

    def guardar_registro():
        try:
            datos = obtener_datos()
            columnas = list(datos.keys())
            parametros = [f":{c}" for c in columnas]

            sql = f"""
                INSERT INTO {NOMBRE_TABLA}
                ({", ".join(columnas)})
                VALUES ({", ".join(parametros)})
            """

            with conectar() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute(sql, datos)
                    conexion.commit()

            limpiar_seleccion()
            consultar_registros()

            messagebox.showinfo(
                "Exito",
                "Proveedor guardado correctamente."
            )

        except ValueError as error:
            messagebox.showerror(
                "Datos incorrectos",
                str(error)
            )

        except oracledb.Error as error:
            messagebox.showerror(
                "Error de Oracle",
                mensaje_error_oracle(error)
            )

    # 7. UPDATE

    def actualizar_registro():
        if id_seleccionado is None:
            messagebox.showwarning(
                "Actualizar",
                "Primero busca un proveedor por ID."
            )
            return

        try:
            datos = obtener_datos()
            datos["id_registro"] = id_seleccionado

            asignaciones = [
                f"{col} = :{col}"
                for _, col in campos
            ]

            sql = f"""
                UPDATE {NOMBRE_TABLA}
                SET {", ".join(asignaciones)}
                WHERE {CLAVE_PRIMARIA} = :id_registro
            """

            with conectar() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute(sql, datos)
                    modificados = cursor.rowcount

                    if modificados == 1:
                        conexion.commit()

            if modificados == 0:
                limpiar_seleccion()
                messagebox.showwarning(
                    "Actualizar",
                    "El proveedor ya no existe."
                )
                consultar_registros()
                return

            consultar_registros()

            messagebox.showinfo(
                "Exito",
                "Proveedor actualizado correctamente."
            )

        except ValueError as error:
            messagebox.showerror(
                "Datos incorrectos",
                str(error)
            )

        except oracledb.Error as error:
            messagebox.showerror(
                "Error de Oracle",
                mensaje_error_oracle(error)
            )

    # 8. DELETE

    def eliminar_registro():
        nonlocal id_seleccionado

        if id_seleccionado is None:
            messagebox.showwarning(
                "Eliminar",
                "Primero busca un proveedor por ID."
            )
            return

        if not messagebox.askyesno(
            "Confirmar eliminacion",
            f"¿Eliminar el proveedor ID {id_seleccionado}?"
        ):
            return

        try:
            with conectar() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute(f"""
                        DELETE FROM {NOMBRE_TABLA}
                        WHERE {CLAVE_PRIMARIA} = :id
                    """, {"id": id_seleccionado})

                    eliminados = cursor.rowcount

                    if eliminados == 1:
                        conexion.commit()

            if eliminados == 0:
                limpiar_seleccion()
                messagebox.showwarning(
                    "Eliminar",
                    "El proveedor ya no existe."
                )
                consultar_registros()
                return

            limpiar_seleccion()
            consultar_registros()

            messagebox.showinfo(
                "Exito",
                "Proveedor eliminado correctamente."
            )

        except oracledb.Error as error:
            messagebox.showerror(
                "Error de Oracle",
                mensaje_error_oracle(error)
            )

    # 9. BOTONES

    ctk.CTkButton(
        buscador,
        text="Buscar ID",
        command=buscar_registro
    ).pack(side="left", padx=10)

    acciones = [
        ("Guardar", guardar_registro),
        ("Consultar", consultar_registros),
        ("Actualizar", actualizar_registro),
    ]

    for texto, funcion in acciones:
        ctk.CTkButton(
            botones,
            text=texto,
            command=funcion
        ).pack(side="left", padx=5)

    ctk.CTkButton(
        botones,
        text="Eliminar",
        command=eliminar_registro,
        fg_color="#B83B3B",
        hover_color="#922D2D"
    ).pack(side="left", padx=5)

    # 10. MOSTRAR REGISTROS AL INICIAR

    consultar_registros()
