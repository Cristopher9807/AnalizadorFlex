import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import subprocess

CARPETA = os.path.dirname(os.path.abspath(__file__))
EJECUTABLE = os.path.join(CARPETA, "analizador.exe")

ventana = tk.Tk()
ventana.title("Analizador Léxico")
ventana.geometry("1100x650")

archivo_actual = {"nombre": None}

# ---------------- Panel izquierdo: lista de archivos ----------------
panel_izquierdo = tk.Frame(ventana)
panel_izquierdo.pack(side="left", fill="y", padx=10, pady=10)

tk.Label(panel_izquierdo, text="Archivos .txt:").pack(anchor="w")

lista_archivos = tk.Listbox(panel_izquierdo, width=30, height=28)
lista_archivos.pack()

def cargar_lista():
    lista_archivos.delete(0, tk.END)
    for nombre in sorted(os.listdir(CARPETA)):
        if nombre.endswith(".txt"):
            lista_archivos.insert(tk.END, nombre)

def al_seleccionar_archivo(event):
    seleccion = lista_archivos.curselection()
    if not seleccion:
        return
    nombre = lista_archivos.get(seleccion[0])
    ruta = os.path.join(CARPETA, nombre)
    with open(ruta, "r", encoding="utf-8") as f:
        contenido = f.read()
    texto_entrada.delete("1.0", tk.END)
    texto_entrada.insert(tk.END, contenido)
    archivo_actual["nombre"] = nombre
    ventana.title(f"Analizador Léxico - {nombre}")

lista_archivos.bind("<<ListboxSelect>>", al_seleccionar_archivo)

def nuevo_archivo():
    nombre = simpledialog.askstring("Nuevo archivo", "Nombre del archivo (sin .txt):")
    if not nombre:
        return
    nombre = nombre.strip() + ".txt"
    ruta = os.path.join(CARPETA, nombre)
    if os.path.exists(ruta):
        messagebox.showerror("Error", "Ya existe un archivo con ese nombre.")
        return
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("")
    cargar_lista()
    texto_entrada.delete("1.0", tk.END)
    archivo_actual["nombre"] = nombre
    ventana.title(f"Analizador Léxico - {nombre}")

def eliminar_archivo():
    seleccion = lista_archivos.curselection()
    if not seleccion:
        messagebox.showwarning("Atención", "Selecciona un archivo primero.")
        return
    nombre = lista_archivos.get(seleccion[0])
    if messagebox.askyesno("Confirmar", f"¿Eliminar {nombre}?"):
        os.remove(os.path.join(CARPETA, nombre))
        cargar_lista()
        texto_entrada.delete("1.0", tk.END)
        archivo_actual["nombre"] = None
        ventana.title("Analizador Léxico")

def guardar_archivo(mostrar_aviso=True):
    if not archivo_actual["nombre"]:
        messagebox.showwarning("Atención", "No hay ningún archivo abierto. Crea uno nuevo primero.")
        return
    ruta = os.path.join(CARPETA, archivo_actual["nombre"])
    contenido = texto_entrada.get("1.0", tk.END)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(contenido)
    if mostrar_aviso:
        messagebox.showinfo("Guardado", "Archivo guardado correctamente.")

botones_frame = tk.Frame(panel_izquierdo)
botones_frame.pack(pady=5, fill="x")

tk.Button(botones_frame, text="Nuevo", command=nuevo_archivo).pack(side="left", expand=True, fill="x")
tk.Button(botones_frame, text="Eliminar", command=eliminar_archivo).pack(side="left", expand=True, fill="x")

# ---------------- Panel derecho: editor + tabla de tokens ----------------
panel_derecho = tk.Frame(ventana)
panel_derecho.pack(side="left", fill="both", expand=True, padx=10, pady=10)

tk.Label(panel_derecho, text="Contenido del archivo:").pack(anchor="w")

texto_entrada = tk.Text(panel_derecho, height=12)
texto_entrada.pack(fill="both", expand=True)

acciones_frame = tk.Frame(panel_derecho)
acciones_frame.pack(fill="x", pady=5)

tk.Button(acciones_frame, text="Guardar", command=guardar_archivo).pack(side="left", padx=5)

def analizar():
    if not archivo_actual["nombre"]:
        messagebox.showwarning("Atención", "Guarda o abre un archivo primero.")
        return
    guardar_archivo(mostrar_aviso=False)
    ruta = os.path.join(CARPETA, archivo_actual["nombre"])

    if not os.path.exists(EJECUTABLE):
        messagebox.showerror("Error", "No se encontró analizador.exe en esta carpeta.")
        return

    resultado = subprocess.run(
        [EJECUTABLE, ruta],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    for fila in tabla_tokens.get_children():
        tabla_tokens.delete(fila)

    lineas = resultado.stdout.splitlines()
    for linea in lineas:
        if "\t" in linea:
            tipo, valor = linea.split("\t", 1)
            tabla_tokens.insert("", tk.END, values=(tipo, valor))

tk.Button(acciones_frame, text="Analizar", command=analizar, bg="#00b894", fg="white").pack(side="left", padx=5)

tk.Label(panel_derecho, text="Tokens generados:").pack(anchor="w", pady=(10, 0))

tabla_tokens = ttk.Treeview(panel_derecho, columns=("tipo", "valor"), show="headings", height=15)
tabla_tokens.heading("tipo", text="Tipo de Token")
tabla_tokens.heading("valor", text="Valor")
tabla_tokens.column("tipo", width=200)
tabla_tokens.column("valor", width=400)
tabla_tokens.pack(fill="both", expand=True)

cargar_lista()

ventana.mainloop()