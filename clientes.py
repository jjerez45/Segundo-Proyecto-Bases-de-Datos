
import customtkinter as ctk
from tkinter import messagebox, ttk
from datetime import datetime, date
import oracledb

from conexion import conectar


def crear_pestana_clientes(pestana):

    # 1. CONFIGURACION

    TABLA = "CLIENTES_P"
    PK = "ID_CLIENTE_P"

    # (etiqueta, columna, max. bytes, obligatorio)
    campos = [
        ("Nombre [max. 50]", "NOMBRE", 50, True),
        ("Apellido [max. 50]", "APELLIDO", 50, True),
        ("Direccion [max. 150]", "DIRECCION", 150, False),
        ("NIT [max. 20]", "NIT", 20, False),
        ("Email [max. 100]", "EMAIL", 100, False),
        ("Telefono [max. 20]", "TELEFONO", 20, False),
        ("Fecha Nacimiento [AAAA-MM-DD]", "FECHA_NACIMIENTO", None, False),
    ]

    columnas_tabla = (
        PK, "NOMBRE", "APELLIDO", "NIT", "EMAIL", "TELEFONO"
    )

    id_seleccionado = None
    entradas = {}

    # 2. INTERFAZ

    ctk.CTkLabel(
        pestana,
        text="GESTION DE CLIENTES",
        font=("Arial", 22, "bold")
    ).pack(pady=10)

    buscador = ctk.CTkFrame(pestana)
    buscador.pack(fill="x", padx=20, pady=5)

    ctk.CTkLabel(
        buscador, text="ID del cliente:"
    ).pack(side="left", padx=10)

    entrada_id = ctk.CTkEntry(
        buscador, width=120, placeholder_text="Ej. 1"
    )
    entrada_id.pack(side="left", padx=5)

    formulario = ctk.CTkScrollableFrame(pestana, height=220)
    formulario.pack(fill="x", padx=20, pady=10)

    for i, (etiqueta, columna, _, _) in enumerate(campos):
        fila = i // 2
        lado = (i % 2) * 2

        ctk.CTkLabel(
            formulario, text=etiqueta
        ).grid(row=fila, column=lado, padx=10, pady=8)

        entrada = ctk.CTkEntry(formulario, width=220)
        entrada.grid(
            row=fila, column=lado + 1, padx=10, pady=8
        )
        entradas[columna] = entrada

    # Marco de botones antes de la tabla
    # para mantenerlos visibles.

    botones = ctk.CTkFrame(pestana)
    botones.pack(side="bottom", pady=5)

    marco_tabla = ctk.CTkFrame(pestana)
    marco_tabla.pack(
        fill="both", expand=True, padx=20, pady=10
    )

    tabla = ttk.Treeview(
        marco_tabla,
        columns=columnas_tabla,
        show="headings",
        height=8
    )

    for columna in columnas_tabla:
        tabla.heading(columna, text=columna)
        tabla.column(columna, width=130, anchor="center")

    barra_v = ttk.Scrollbar(
        marco_tabla, orient="vertical", command=tabla.yview
    )
    barra_h = ttk.Scrollbar(
        marco_tabla, orient="horizontal", command=tabla.xview
    )

    tabla.configure(
        yscrollcommand=barra_v.set,
        xscrollcommand=barra_h.set
    )

    marco_tabla.grid_rowconfigure(0, weight=1)
    marco_tabla.grid_columnconfigure(0, weight=1)

    tabla.grid(row=0, column=0, sticky="nsew")
    barra_v.grid(row=0, column=1, sticky="ns")
    barra_h.grid(row=1, column=0, sticky="ew")

    # 3. AUXILIARES

    def limpiar_formulario():
        for entrada in entradas.values():
            entrada.delete(0, "end")

    def mostrar_error_oracle(error):
        codigo = (
            getattr(error.args[0], "code", None)
            if error.args else None
        )

        mensajes = {
            1: "El NIT ya existe.",
            1400: "Falta un campo obligatorio.",
            2292: (
                "No se puede eliminar: "
                "el cliente tiene registros relacionados."
            ),
            12899: "Un texto supera la longitud permitida."
        }

        messagebox.showerror(
            "Error de Oracle",
            mensajes.get(codigo, str(error))
        )

    def obtener_datos():
        datos = {}

        for etiqueta, columna, maximo, obligatorio in campos:
            texto = entradas[columna].get().strip()

            if not texto:
                if obligatorio:
                    raise ValueError(
                        f"{columna} es obligatorio."
                    )
                datos[columna] = None
                continue

            if columna == "FECHA_NACIMIENTO":
                try:
                    datos[columna] = datetime.strptime(
                        texto, "%Y-%m-%d"
                    )
                except ValueError:
                    raise ValueError(
                        "FECHA_NACIMIENTO debe tener "
                        "formato AAAA-MM-DD."
                    )
                continue

            if len(texto.encode("utf-8")) > maximo:
                raise ValueError(
                    f"{columna} supera {maximo} bytes."
                )

            if columna == "EMAIL" and "@" not in texto:
                raise ValueError("EMAIL no es valido.")

            datos[columna] = texto

        return datos

    # 4. CONSULTAR

    def consultar_clientes():
        try:
            with conectar() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute(f"""
                        SELECT {", ".join(columnas_tabla)}
                        FROM {TABLA}
                        ORDER BY {PK}
                    """)
                    registros = cursor.fetchall()

            for item in tabla.get_children():
                tabla.delete(item)

            for registro in registros:
                tabla.insert(
                    "", "end",
                    values=[
                        "" if d is None else str(d)
                        for d in registro
                    ]
                )

        except oracledb.Error as error:
            mostrar_error_oracle(error)

    # 5. BUSCAR POR ID

    def buscar_cliente():
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
        columnas = [col for _, col, _, _ in campos]

        try:
            with conectar() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute(f"""
                        SELECT {", ".join(columnas)}
                        FROM {TABLA}
                        WHERE {PK} = :id
                    """, {"id": id_buscado})

                    registro = cursor.fetchone()

            if registro is None:
                limpiar_formulario()
                messagebox.showinfo(
                    "Busqueda", "No existe ese cliente."
                )
                return

            for columna, valor in zip(columnas, registro):
                if isinstance(valor, (datetime, date)):
                    texto = valor.strftime("%Y-%m-%d")
                else:
                    texto = (
                        "" if valor is None else str(valor)
                    )

                entradas[columna].delete(0, "end")
                entradas[columna].insert(0, texto)

            id_seleccionado = id_buscado

            consultar_clientes()

            for item in tabla.get_children():
                if str(
                    tabla.item(item, "values")[0]
                ) != str(id_buscado):
                    tabla.delete(item)

            messagebox.showinfo(
                "Busqueda",
                "Cliente cargado en el formulario."
            )

        except oracledb.Error as error:
            mostrar_error_oracle(error)

    # 6. INSERT

    def guardar_cliente():
        nonlocal id_seleccionado

        try:
            datos = obtener_datos()
            columnas = list(datos.keys())

            sql = f"""
                INSERT INTO {TABLA} ({", ".join(columnas)})
                VALUES ({", ".join(":" + c for c in columnas)})
            """

            with conectar() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute(sql, datos)
                    conexion.commit()

            id_seleccionado = None
            entrada_id.delete(0, "end")
            limpiar_formulario()
            consultar_clientes()

            messagebox.showinfo(
                "Exito", "Cliente guardado correctamente."
            )

        except ValueError as error:
            messagebox.showerror(
                "Datos incorrectos", str(error)
            )

        except oracledb.Error as error:
            mostrar_error_oracle(error)

    # 7. UPDATE

    def actualizar_cliente():

        if id_seleccionado is None:
            messagebox.showwarning(
                "Actualizar",
                "Primero busca un cliente por ID."
            )
            return

        try:
            datos = obtener_datos()
            asignaciones = ", ".join(
                f"{c} = :{c}" for c in datos
            )
            datos["id_registro"] = id_seleccionado

            with conectar() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute(f"""
                        UPDATE {TABLA}
                        SET {asignaciones}
                        WHERE {PK} = :id_registro
                    """, datos)

                    modificados = cursor.rowcount

                    if modificados == 1:
                        conexion.commit()

            if modificados == 0:
                messagebox.showwarning(
                    "Actualizar",
                    "El cliente ya no existe."
                )
                return

            consultar_clientes()
            messagebox.showinfo(
                "Exito",
                "Cliente actualizado correctamente."
            )

        except ValueError as error:
            messagebox.showerror(
                "Datos incorrectos", str(error)
            )

        except oracledb.Error as error:
            mostrar_error_oracle(error)

    # 8. DELETE

    def eliminar_cliente():
        nonlocal id_seleccionado

        if id_seleccionado is None:
            messagebox.showwarning(
                "Eliminar",
                "Primero busca un cliente por ID."
            )
            return

        if not messagebox.askyesno(
            "Confirmar eliminacion",
            f"¿Eliminar el cliente ID {id_seleccionado}?"
        ):
            return

        try:
            with conectar() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute(f"""
                        DELETE FROM {TABLA}
                        WHERE {PK} = :id
                    """, {"id": id_seleccionado})

                    eliminados = cursor.rowcount

                    if eliminados == 1:
                        conexion.commit()

            if eliminados == 0:
                messagebox.showwarning(
                    "Eliminar",
                    "El cliente ya no existe."
                )
                return

            id_seleccionado = None
            entrada_id.delete(0, "end")
            limpiar_formulario()
            consultar_clientes()

            messagebox.showinfo(
                "Exito",
                "Cliente eliminado correctamente."
            )

        except oracledb.Error as error:
            mostrar_error_oracle(error)

    # 9. BOTONES

    ctk.CTkButton(
        buscador,
        text="Buscar ID",
        width=100,
        command=buscar_cliente
    ).pack(side="left", padx=10)

    for texto, funcion in [
        ("Guardar", guardar_cliente),
        ("Consultar", consultar_clientes),
        ("Actualizar", actualizar_cliente),
    ]:
        ctk.CTkButton(
            botones,
            text=texto,
            command=funcion
        ).pack(side="left", padx=8)

    ctk.CTkButton(
        botones,
        text="Eliminar",
        command=eliminar_cliente,
        fg_color="#B83B3B",
        hover_color="#922D2D"
    ).pack(side="left", padx=8)

    # 10. MOSTRAR DATOS AL INICIAR

    consultar_clientes()
