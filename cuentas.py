
import customtkinter as ctk
from tkinter import messagebox, ttk
from decimal import Decimal, InvalidOperation
import oracledb

from conexion import conectar


# =========================================
# MENSAJES DE ERROR DE ORACLE
# =========================================

def mensaje_error_oracle(error):

    detalle = error.args[0] if error.args else None
    codigo = getattr(detalle, "code", None)

    if codigo == 1:
        return "Ya existe un registro con un valor que debe ser unico."

    if codigo == 1400:
        return "Falta completar un campo obligatorio."

    if codigo == 12899:
        return "Uno de los textos supera la longitud permitida."

    if codigo == 2292:
        return (
            "No se puede eliminar la cuenta porque "
            "tiene registros relacionados."
        )

    if codigo == 1438:
        return "El saldo supera la precision permitida por Oracle."

    return str(error)


# =========================================
# MODULO DE CUENTAS BANCARIAS
# =========================================

def crear_pestana_cuentas(pestana):

    # 1. CONFIGURACION

    tabla_nombre = "CUENTAS_BANCARIAS_P"
    clave = "ID_CUENTA_BANCARIA_P"

    campos = [
        ("Banco", "BANCO"),
        ("Numero de cuenta", "NUMERO_CUENTA"),
        ("Tipo de cuenta", "TIPO_CUENTA"),
        ("Saldo inicial", "SALDO")
    ]

    columnas = (
        clave,
        "BANCO",
        "NUMERO_CUENTA",
        "TIPO_CUENTA",
        "SALDO"
    )

    entradas = {}
    id_seleccionado = None

    # 2. TITULO

    ctk.CTkLabel(
        pestana,
        text="GESTION DE CUENTAS BANCARIAS",
        font=("Arial", 22, "bold")
    ).pack(pady=10)

    # 3. FORMULARIO

    formulario = ctk.CTkFrame(pestana)
    formulario.pack(
        fill="x",
        padx=15,
        pady=10
    )

    for i, (etiqueta, columna) in enumerate(campos):

        ctk.CTkLabel(
            formulario,
            text=etiqueta
        ).grid(
            row=i,
            column=0,
            padx=10,
            pady=6
        )

        entrada = ctk.CTkEntry(
            formulario,
            width=250
        )

        entrada.grid(
            row=i,
            column=1,
            padx=10,
            pady=6
        )

        entradas[columna] = entrada

    # 4. BUSCADOR

    buscador = ctk.CTkFrame(pestana)
    buscador.pack(
        fill="x",
        padx=15,
        pady=5
    )

    ctk.CTkLabel(
        buscador,
        text="ID de cuenta:"
    ).pack(
        side="left",
        padx=5
    )

    entrada_id = ctk.CTkEntry(
        buscador,
        width=100,
        placeholder_text="Ej. 1"
    )

    entrada_id.pack(
        side="left",
        padx=5
    )

    # 5. BOTONES
    # Se reserva su espacio antes de la tabla.

    botones = ctk.CTkFrame(pestana)
    botones.pack(
        side="bottom",
        pady=10
    )

    # 6. TABLA VISUAL

    marco = ctk.CTkFrame(pestana)
    marco.pack(
        fill="both",
        expand=True,
        padx=15,
        pady=10
    )

    tabla = ttk.Treeview(
        marco,
        columns=columnas,
        show="headings",
        height=8
    )

    for columna in columnas:

        tabla.heading(
            columna,
            text=columna
        )

        tabla.column(
            columna,
            width=150,
            anchor="center"
        )

    barra_vertical = ttk.Scrollbar(
        marco,
        orient="vertical",
        command=tabla.yview
    )

    barra_horizontal = ttk.Scrollbar(
        marco,
        orient="horizontal",
        command=tabla.xview
    )

    tabla.configure(
        yscrollcommand=barra_vertical.set,
        xscrollcommand=barra_horizontal.set
    )

    marco.grid_rowconfigure(0, weight=1)
    marco.grid_columnconfigure(0, weight=1)

    tabla.grid(
        row=0,
        column=0,
        sticky="nsew"
    )

    barra_vertical.grid(
        row=0,
        column=1,
        sticky="ns"
    )

    barra_horizontal.grid(
        row=1,
        column=0,
        sticky="ew"
    )

    # =========================================
    # 7. LIMPIAR FORMULARIO
    # =========================================

    def limpiar():

        nonlocal id_seleccionado

        id_seleccionado = None
        entrada_id.delete(0, "end")

        for entrada in entradas.values():
            entrada.delete(0, "end")

    # =========================================
    # 8. VALIDAR DATOS
    # =========================================

    def obtener_datos():

        banco = entradas["BANCO"].get().strip()
        numero = entradas["NUMERO_CUENTA"].get().strip()
        tipo = entradas["TIPO_CUENTA"].get().strip()
        saldo_texto = entradas["SALDO"].get().strip()

        if not banco or not numero or not tipo or not saldo_texto:
            raise ValueError(
                "Completa todos los campos."
            )

        try:
            saldo = Decimal(saldo_texto)

        except InvalidOperation:
            raise ValueError(
                "El saldo debe ser un numero valido."
            )

        if not saldo.is_finite():
            raise ValueError(
                "El saldo debe ser un numero finito."
            )

        if saldo < 0:
            raise ValueError(
                "El saldo no puede ser negativo."
            )

        if saldo.as_tuple().exponent < -2:
            raise ValueError(
                "El saldo solo admite hasta dos decimales."
            )

        datos = {
            "BANCO": banco,
            "NUMERO_CUENTA": numero,
            "TIPO_CUENTA": tipo,
            "SALDO": saldo
        }

        return datos

    # =========================================
    # 9. CONSULTAR
    # =========================================

    def consultar():

        try:
            with conectar() as conexion:
                with conexion.cursor() as cursor:

                    cursor.execute(f"""
                        SELECT {", ".join(columnas)}
                        FROM {tabla_nombre}
                        ORDER BY {clave}
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

    # =========================================
    # 10. GUARDAR
    # =========================================

    def guardar():

        try:
            datos = obtener_datos()

            with conectar() as conexion:
                with conexion.cursor() as cursor:

                    cursor.execute("""
                        INSERT INTO CUENTAS_BANCARIAS_P
                        (
                            BANCO,
                            NUMERO_CUENTA,
                            TIPO_CUENTA,
                            SALDO
                        )
                        VALUES
                        (
                            :BANCO,
                            :NUMERO_CUENTA,
                            :TIPO_CUENTA,
                            :SALDO
                        )
                    """, datos)

                    conexion.commit()

            limpiar()
            consultar()

            messagebox.showinfo(
                "Exito",
                "Cuenta bancaria guardada correctamente."
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

    # =========================================
    # 11. BUSCAR POR ID
    # =========================================

    def buscar():

        nonlocal id_seleccionado

        texto = entrada_id.get().strip()

        if not texto.isdecimal() or int(texto) <= 0:

            messagebox.showwarning(
                "Validacion",
                "Introduce un ID entero positivo."
            )
            return

        id_buscado = int(texto)

        # Evitar conservar una seleccion anterior
        id_seleccionado = None

        try:
            with conectar() as conexion:
                with conexion.cursor() as cursor:

                    cursor.execute("""
                        SELECT
                            BANCO,
                            NUMERO_CUENTA,
                            TIPO_CUENTA,
                            SALDO
                        FROM CUENTAS_BANCARIAS_P
                        WHERE ID_CUENTA_BANCARIA_P = :id
                    """, {"id": id_buscado})

                    registro = cursor.fetchone()

            if registro is None:

                limpiar()

                messagebox.showinfo(
                    "Busqueda",
                    "No se encontro la cuenta."
                )

                consultar()
                return

            limpiar()

            for (_, columna), valor in zip(campos, registro):

                entradas[columna].insert(
                    0,
                    "" if valor is None else str(valor)
                )

            id_seleccionado = id_buscado
            entrada_id.insert(0, str(id_buscado))

            # Mostrar solo la cuenta encontrada
            consultar()

            for item in tabla.get_children():

                valores = tabla.item(item, "values")

                if str(valores[0]) != str(id_buscado):
                    tabla.delete(item)

            messagebox.showinfo(
                "Busqueda",
                "Cuenta bancaria cargada correctamente."
            )

        except oracledb.Error as error:

            messagebox.showerror(
                "Error de Oracle",
                mensaje_error_oracle(error)
            )

    # =========================================
    # 12. ACTUALIZAR
    # =========================================

    def actualizar():

        if id_seleccionado is None:

            messagebox.showwarning(
                "Actualizar",
                "Primero busca una cuenta por ID."
            )
            return

        try:
            datos = obtener_datos()
            datos["id"] = id_seleccionado

            with conectar() as conexion:
                with conexion.cursor() as cursor:

                    cursor.execute("""
                        UPDATE CUENTAS_BANCARIAS_P
                        SET
                            BANCO = :BANCO,
                            NUMERO_CUENTA = :NUMERO_CUENTA,
                            TIPO_CUENTA = :TIPO_CUENTA,
                            SALDO = :SALDO
                        WHERE ID_CUENTA_BANCARIA_P = :id
                    """, datos)

                    modificados = cursor.rowcount

                    if modificados == 1:
                        conexion.commit()

            if modificados == 0:

                limpiar()
                consultar()

                messagebox.showwarning(
                    "Actualizar",
                    "La cuenta ya no existe."
                )
                return

            consultar()

            messagebox.showinfo(
                "Exito",
                "Cuenta bancaria actualizada correctamente."
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

    # =========================================
    # 13. ELIMINAR
    # =========================================

    def eliminar():

        if id_seleccionado is None:

            messagebox.showwarning(
                "Eliminar",
                "Primero busca una cuenta por ID."
            )
            return

        confirmar = messagebox.askyesno(
            "Confirmar eliminacion",
            f"¿Deseas eliminar la cuenta ID {id_seleccionado}?"
        )

        if not confirmar:
            return

        try:
            with conectar() as conexion:
                with conexion.cursor() as cursor:

                    cursor.execute("""
                        DELETE FROM CUENTAS_BANCARIAS_P
                        WHERE ID_CUENTA_BANCARIA_P = :id
                    """, {"id": id_seleccionado})

                    eliminados = cursor.rowcount

                    if eliminados == 1:
                        conexion.commit()

            if eliminados == 0:

                limpiar()
                consultar()

                messagebox.showwarning(
                    "Eliminar",
                    "La cuenta ya no existe."
                )
                return

            limpiar()
            consultar()

            messagebox.showinfo(
                "Exito",
                "Cuenta bancaria eliminada correctamente."
            )

        except oracledb.Error as error:

            messagebox.showerror(
                "Error de Oracle",
                mensaje_error_oracle(error)
            )

    # =========================================
    # 14. BOTONES
    # =========================================

    ctk.CTkButton(
        buscador,
        text="Buscar ID",
        command=buscar
    ).pack(
        side="left",
        padx=5
    )

    acciones = [
        ("Guardar", guardar),
        ("Consultar", consultar),
        ("Actualizar", actualizar),
        ("Eliminar", eliminar),
        ("Limpiar", limpiar)
    ]

    for texto, funcion in acciones:

        ctk.CTkButton(
            botones,
            text=texto,
            command=funcion
        ).pack(
            side="left",
            padx=4,
            pady=5
        )

    # =========================================
    # 15. CONSULTAR AL INICIAR
    # =========================================

    consultar()
