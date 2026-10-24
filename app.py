
import customtkinter as ctk

from productos import crear_pestana_productos
from facturas import crear_pestana_facturas
from clientes import crear_pestana_clientes
from proveedores import crear_pestana_proveedores
from cuentas import crear_pestana_cuentas


# CONFIGURACION DE APARIENCIA

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# VENTANA PRINCIPAL

app = ctk.CTk()
app.title("Sistema Contable")
app.geometry("1100x700")
app.minsize(950, 600)


# TITULO PRINCIPAL

titulo = ctk.CTkLabel(
    app,
    text="SISTEMA CONTABLE",
    font=("Arial", 26, "bold")
)
titulo.pack(pady=20)


# CREACION DE PESTANAS

pestanas = ctk.CTkTabview(app)
pestanas.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=10
)

nombres = [
    "Productos",
    "Facturas",
    "Clientes",
    "Proveedores",
    "Cuentas Bancarias"
]

for nombre in nombres:
    pestanas.add(nombre)


# MODULOS INTEGRADOS

crear_pestana_productos(
    pestanas.tab("Productos")
)

crear_pestana_facturas(
    pestanas.tab("Facturas")
)

crear_pestana_clientes(
    pestanas.tab("Clientes")
)

crear_pestana_proveedores(
    pestanas.tab("Proveedores")
)

crear_pestana_cuentas(
    pestanas.tab("Cuentas Bancarias")
)


# INICIAR APLICACION

app.mainloop()
