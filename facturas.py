
import customtkinter as ctk
from tkinter import messagebox, ttk
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
import oracledb

from conexion import conectar


def crear_pestana_facturas(pestana):

    # ==========================================
    # 1. TITULO Y BUSCADOR
    # ==========================================

    titulo = ctk.CTkLabel(
        pestana,
        text="GESTION DE FACTURAS DE VENTA",
        font=("Arial", 22, "bold")
    )
    titulo.pack(pady=10)

    buscador = ctk.CTkFrame(pestana)
    buscador.pack(fill="x", padx=20, pady=5)

    ctk.CTkLabel(
        buscador,
        text="ID de la factura:"
    ).pack(side="left", padx=10)

    entrada_id = ctk.CTkEntry(
        buscador,
        width=120,
        placeholder_text="Ej. 1"
    )
    entrada_id.pack(side="left", padx=5)

    id_seleccionado = None

    # ==========================================
    # 2. CAMPOS DEL FORMULARIO
    # ==========================================

    formulario = ctk.CTkScrollableFrame(
        pestana,
        height=260
    )
    formulario.pack(fill="x", padx=20, pady=10)

    campos = [
        ("ID Cliente [ENTERO - FK]", "ID_CLIENTE_P"),
        ("Numero Factura [max. 30]", "NUMERO_FACTURA"),
        ("Direccion Sede [max. 150]", "DIRECCION_SEDE"),
        ("Descuento [DECIMAL 10,2]", "DESCUENTO"),
        ("Impuesto [DECIMAL 10,2]", "IMPUESTO"),
        ("Total [DECIMAL 10,2]", "TOTAL"),
        ("Metodo Pago [max. 30]", "METODO_PAGO"),
        ("Saldo Pendiente [DECIMAL 10,2]", "SALDO_PENDIENTE"),
        ("Fecha Vencimiento [AAAA-MM-DD]", "FECHA_VENCIMIENTO")
    ]

    entradas = {}

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

    # FECHA_HORA no se pide al crear.
    # Oracle utiliza CURRENT_TIMESTAMP.

    # ==========================================
    # 3. TABLA VISUAL TREEVIEW
    # ==========================================

    marco_tabla = ctk.CTkFrame(pestana)
    marco_tabla.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=10
    )

    columnas_tabla = (
        "ID",
        "CLIENTE",
        "FECHA",
        "NUMERO",
        "TOTAL",
        "PAGO",
        "SALDO"
    )

    tabla = ttk.Treeview(
        marco_tabla,
        columns=columnas_tabla,
        show="headings",
        height=8
    )

    anchos = {
        "ID": 65,
        "CLIENTE": 85,
        "FECHA": 165,
        "NUMERO": 130,
        "TOTAL": 110,
        "PAGO": 120,
        "SALDO": 110
    }

    for columna in columnas_tabla:
        tabla.heading(columna, text=columna)
        tabla.column(
            columna,
            width=anchos[columna],
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

    # ==========================================
    # 4. FUNCIONES AUXILIARES
    # ==========================================

    def limpiar_formulario():

        for entrada in entradas.values():
            entrada.delete(0, "end")

    def mostrar_error_oracle(error):

        codigo = getattr(
            error.args[0],
            "code",
            None
        ) if error.args else None

        mensajes = {
            1: "El numero de factura ya existe.",
            2291: "El ID del cliente no existe.",
            2292: (
                "No se puede eliminar esta factura "
                "porque tiene registros relacionados."
            ),
            1400: "Falta un campo obligatorio.",
            1438: "Un numero supera la precision permitida.",
            12899: "Un texto supera la longitud permitida."
        }

        mensaje = mensajes.get(
            codigo,
            str(error)
        )

        messagebox.showerror(
            "Error de Oracle",
            mensaje
        )

    def validar_decimal(campo, obligatorio=False):

        texto = entradas[campo].get().strip()

        if not texto:
            if obligatorio:
                raise ValueError(
                    f"{campo} es obligatorio."
                )
            return None

        try:
            numero = Decimal(texto)
        except InvalidOperation:
            raise ValueError(
                f"{campo} debe ser un numero decimal."
            )

        if not numero.is_finite() or numero < 0:
            raise ValueError(
                f"{campo} debe ser un numero no negativo."
            )

        # Los campos monetarios admiten
        # como maximo dos decimales.
        if numero.as_tuple().exponent < -2:
            raise ValueError(
                f"{campo} admite maximo 2 decimales."
            )

        if campo != "TOTAL" and numero >= Decimal("100000000"):
            raise ValueError(
                f"{campo} supera NUMBER(10,2)."
            )

        return numero

    def validar_texto(campo, maximo):

        texto = entradas[campo].get().strip()

        if len(texto.encode("utf-8")) > maximo:
            raise ValueError(
                f"{campo} supera {maximo} bytes."
            )

        return texto or None

    def validar_fecha(campo):

        texto = entradas[campo].get().strip()

        if not texto:
            return None

        try:
            return datetime.strptime(
                texto,
                "%Y-%m-%d"
            )
        except ValueError:
            raise ValueError(
                f"{campo} debe tener formato AAAA-MM-DD."
            )

    def obtener_datos():

        cliente_texto = entradas[
            "ID_CLIENTE_P"
        ].get().strip()

        if not cliente_texto.isdecimal():
            raise ValueError(
                "El ID del cliente debe ser un entero positivo."
            )

        cliente = int(cliente_texto)

        if cliente <= 0:
            raise ValueError(
                "El ID del cliente debe ser positivo."
            )

        datos = {
            "cliente": cliente,
            "numero": validar_texto(
                "NUMERO_FACTURA", 30
            ),
            "direccion": validar_texto(
                "DIRECCION_SEDE", 150
            ),
            "descuento": validar_decimal(
                "DESCUENTO"
            ),
            "impuesto": validar_decimal(
                "IMPUESTO"
            ),
            "total": validar_decimal(
                "TOTAL", obligatorio=True
            ),
            "metodo": validar_texto(
                "METODO_PAGO", 30
            ),
            "saldo": validar_decimal(
                "SALDO_PENDIENTE"
            ),
            "vencimiento": validar_fecha(
                "FECHA_VENCIMIENTO"
            )
        }

        return datos

    # ==========================================
    # 5. CONSULTAR TODAS LAS FACTURAS
    # ==========================================

    def consultar_facturas():

        try:
            with conectar() as conexion:
                with conexion.cursor() as cursor:

                    cursor.execute("""
                        SELECT
                            ID_FACTURA_VENTA_P,
                            ID_CLIENTE_P,
                            FECHA_HORA,
                            NUMERO_FACTURA,
                            TOTAL,
                            METODO_PAGO,
                            SALDO_PENDIENTE
                        FROM FACTURAS_VENTA_P
                        ORDER BY ID_FACTURA_VENTA_P
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
            mostrar_error_oracle(error)

    # ==========================================
    # 6. BUSCAR FACTURA POR ID
    # ==========================================

    def buscar_factura():

        nonlocal id_seleccionado

        texto_id = entrada_id.get().strip()

        if not texto_id.isdecimal() or int(texto_id) <= 0:
            messagebox.showwarning(
                "Validacion",
                "Introduce un ID entero positivo."
            )
            return

        id_factura = int(texto_id)
        id_seleccionado = None

        try:
            with conectar() as conexion:
                with conexion.cursor() as cursor:

                    cursor.execute("""
                        SELECT
                            ID_CLIENTE_P,
                            NUMERO_FACTURA,
                            DIRECCION_SEDE,
                            DESCUENTO,
                            IMPUESTO,
                            TOTAL,
                            METODO_PAGO,
                            SALDO_PENDIENTE,
                            FECHA_VENCIMIENTO,
                            FECHA_HORA
                        FROM FACTURAS_VENTA_P
                        WHERE ID_FACTURA_VENTA_P = :id
                    """, {"id": id_factura})

                    factura = cursor.fetchone()

            if factura is None:
                limpiar_formulario()

                for item in tabla.get_children():
                    tabla.delete(item)

                messagebox.showinfo(
                    "Busqueda",
                    "No existe una factura con ese ID."
                )
                return

            columnas = [
                "ID_CLIENTE_P",
                "NUMERO_FACTURA",
                "DIRECCION_SEDE",
                "DESCUENTO",
                "IMPUESTO",
                "TOTAL",
                "METODO_PAGO",
                "SALDO_PENDIENTE",
                "FECHA_VENCIMIENTO"
            ]

            for columna, valor in zip(columnas, factura):

                if isinstance(valor, (datetime, date)):
                    texto = valor.strftime("%Y-%m-%d")
                else:
                    texto = "" if valor is None else str(valor)

                entradas[columna].delete(0, "end")
                entradas[columna].insert(0, texto)

            id_seleccionado = id_factura

            for item in tabla.get_children():
                tabla.delete(item)

            tabla.insert(
                "",
                "end",
                values=(
                    id_factura,
                    factura[0],
                    factura[9],
                    factura[1],
                    factura[5],
                    factura[6],
                    factura[7]
                )
            )

            messagebox.showinfo(
                "Busqueda",
                "Factura cargada en el formulario."
            )

        except oracledb.Error as error:
            mostrar_error_oracle(error)

    # ==========================================
    # 7. GUARDAR FACTURA - INSERT
    # ==========================================

    def guardar_factura():

        nonlocal id_seleccionado

        try:
            datos = obtener_datos()

            # Respetar los DEFAULT de Oracle.
            # Si un campo opcional esta vacio,
            # lo omitimos del INSERT.
            columnas = [
                ("ID_CLIENTE_P", "cliente"),
                ("NUMERO_FACTURA", "numero"),
                ("DIRECCION_SEDE", "direccion"),
                ("DESCUENTO", "descuento"),
                ("IMPUESTO", "impuesto"),
                ("TOTAL", "total"),
                ("METODO_PAGO", "metodo"),
                ("SALDO_PENDIENTE", "saldo"),
                ("FECHA_VENCIMIENTO", "vencimiento")
            ]

            presentes = [
                (columna, clave)
                for columna, clave in columnas
                if datos[clave] is not None
            ]

            nombres = ", ".join(
                columna for columna, clave in presentes
            )

            parametros = ", ".join(
                ":" + clave for columna, clave in presentes
            )

            sql = f"""
                INSERT INTO FACTURAS_VENTA_P
                ({nombres})
                VALUES ({parametros})
            """

            with conectar() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute(sql, datos)
                    conexion.commit()

            id_seleccionado = None
            entrada_id.delete(0, "end")
            limpiar_formulario()
            consultar_facturas()

            messagebox.showinfo(
                "Exito",
                "Factura guardada correctamente."
            )

        except (ValueError, InvalidOperation) as error:
            messagebox.showerror(
                "Datos incorrectos",
                str(error)
            )

        except oracledb.Error as error:
            mostrar_error_oracle(error)

    # ==========================================
    # 8. ACTUALIZAR FACTURA - UPDATE
    # ==========================================

    def actualizar_factura():

        if id_seleccionado is None:
            messagebox.showwarning(
                "Actualizar",
                "Primero busca una factura por ID."
            )
            return

        try:
            datos = obtener_datos()
            datos["id_factura"] = id_seleccionado

            with conectar() as conexion:
                with conexion.cursor() as cursor:

                    cursor.execute("""
                        UPDATE FACTURAS_VENTA_P
                        SET ID_CLIENTE_P = :cliente,
                            NUMERO_FACTURA = :numero,
                            DIRECCION_SEDE = :direccion,
                            DESCUENTO = :descuento,
                            IMPUESTO = :impuesto,
                            TOTAL = :total,
                            METODO_PAGO = :metodo,
                            SALDO_PENDIENTE = :saldo,
                            FECHA_VENCIMIENTO = :vencimiento
                        WHERE ID_FACTURA_VENTA_P = :id_factura
                    """, datos)

                    modificados = cursor.rowcount

                    if modificados == 1:
                        conexion.commit()

            if modificados == 0:
                messagebox.showwarning(
                    "Actualizar",
                    "La factura ya no existe."
                )
                return

            consultar_facturas()

            messagebox.showinfo(
                "Exito",
                "Factura actualizada correctamente."
            )

        except (ValueError, InvalidOperation) as error:
            messagebox.showerror(
                "Datos incorrectos",
                str(error)
            )

        except oracledb.Error as error:
            mostrar_error_oracle(error)

    # ==========================================
    # 9. ELIMINAR FACTURA - DELETE
    # ==========================================

    def eliminar_factura():

        nonlocal id_seleccionado

        if id_seleccionado is None:
            messagebox.showwarning(
                "Eliminar",
                "Primero busca una factura por ID."
            )
            return

        confirmar = messagebox.askyesno(
            "Confirmar eliminacion",
            f"¿Deseas eliminar la factura ID {id_seleccionado}?"
        )

        if not confirmar:
            return

        try:
            with conectar() as conexion:
                with conexion.cursor() as cursor:

                    cursor.execute("""
                        DELETE FROM FACTURAS_VENTA_P
                        WHERE ID_FACTURA_VENTA_P = :id
                    """, {"id": id_seleccionado})

                    eliminados = cursor.rowcount

                    if eliminados == 1:
                        conexion.commit()

            if eliminados == 0:
                messagebox.showwarning(
                    "Eliminar",
                    "La factura ya no existe."
                )
                return

            id_seleccionado = None
            entrada_id.delete(0, "end")
            limpiar_formulario()
            consultar_facturas()

            messagebox.showinfo(
                "Exito",
                "Factura eliminada correctamente."
            )

        except oracledb.Error as error:
            mostrar_error_oracle(error)

    # ==========================================
    # 10. BOTONES
    # ==========================================

    botones = ctk.CTkFrame(pestana)
    botones.pack(pady=5)

    ctk.CTkButton(
        buscador,
        text="Buscar ID",
        command=buscar_factura,
        width=100
    ).pack(side="left", padx=10)

    ctk.CTkButton(
        botones,
        text="Guardar factura",
        command=guardar_factura
    ).pack(side="left", padx=8)

    ctk.CTkButton(
        botones,
        text="Consultar facturas",
        command=consultar_facturas
    ).pack(side="left", padx=8)

    ctk.CTkButton(
        botones,
        text="Actualizar",
        command=actualizar_factura
    ).pack(side="left", padx=8)

    ctk.CTkButton(
        botones,
        text="Eliminar",
        command=eliminar_factura,
        fg_color="#B83B3B",
        hover_color="#922D2D"
    ).pack(side="left", padx=8)

    # ==========================================
    # 11. MOSTRAR FACTURAS AL INICIAR
    # ==========================================

    consultar_facturas()
