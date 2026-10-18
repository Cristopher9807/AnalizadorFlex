import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import os
import shutil
import subprocess
import sys
import unicodedata

from parser import tokens_desde_salida, analizar_sintaxis
from semantico import analizar_semantica
from traductor import traducir, DESTINOS, EXTENSIONES, ErrorTraduccion

if getattr(sys, "frozen", False):
    # Corriendo como .exe: los .txt están junto al .exe (carpeta EJECUTABLE)
    CARPETA = os.path.dirname(os.path.abspath(sys.executable))
    EJECUTABLE = os.path.join(sys._MEIPASS, "analizador.exe")
else:
    # Corriendo con "python interfaz.py": el analizador.exe está en la raíz del proyecto
    # y los .txt se leen de la carpeta EJECUTABLE, igual que hace el .exe final.
    CARPETA_PROYECTO = os.path.dirname(os.path.abspath(__file__))
    CARPETA = os.path.join(CARPETA_PROYECTO, "EJECUTABLE")
    os.makedirs(CARPETA, exist_ok=True)
    EJECUTABLE = os.path.join(CARPETA_PROYECTO, "analizador.exe")

PREFIJO_SEMANTICO = "Semantico"
TITULO_BASE = "Analizador Léxico / Sintáctico / Semántico / Traductor"

ventana = tk.Tk()
ventana.title(TITULO_BASE)
ventana.geometry("1100x800")

archivo_actual = {"nombre": None}

# Archivos abiertos manualmente: se muestran siempre en la lista, sin importar el filtro del modo
archivos_extra = set()

# Última traducción generada (para el botón "Guardar traducción")
ultima_traduccion = {"codigo": None, "destino": None}

# ---------------- Panel izquierdo: lista de archivos ----------------
panel_izquierdo = tk.Frame(ventana)
panel_izquierdo.pack(side="left", fill="y", padx=10, pady=10)

tk.Label(panel_izquierdo, text="Archivos .txt:").pack(anchor="w")

lista_archivos = tk.Listbox(panel_izquierdo, width=30, height=28)
lista_archivos.pack()


def es_archivo_semantico(nombre):
    """True si el nombre empieza por 'semantico', ignorando tildes y mayúsculas."""
    limpio = unicodedata.normalize("NFD", nombre)
    limpio = "".join(c for c in limpio if unicodedata.category(c) != "Mn")
    return limpio.lower().startswith("semantico")


def cargar_lista():
    """Modo Semántico: archivos 'Semantico ...'. Otros modos (incluido Traductor): el resto.
    Los archivos abiertos con 'Abrir...' se muestran siempre."""
    lista_archivos.delete(0, tk.END)
    modo_semantico = modo_var.get() == "Semántico"
    for nombre in sorted(os.listdir(CARPETA)):
        if not nombre.endswith(".txt"):
            continue
        if es_archivo_semantico(nombre) == modo_semantico or nombre in archivos_extra:
            lista_archivos.insert(tk.END, nombre)
    seleccionar_en_lista(archivo_actual["nombre"])


def seleccionar_en_lista(nombre):
    """Resalta en la lista el archivo indicado (si está)."""
    lista_archivos.selection_clear(0, tk.END)
    if not nombre:
        return
    nombres = lista_archivos.get(0, tk.END)
    if nombre in nombres:
        indice = nombres.index(nombre)
        lista_archivos.selection_set(indice)
        lista_archivos.see(indice)


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
    ventana.title(f"Analizador - {nombre}")


lista_archivos.bind("<<ListboxSelect>>", al_seleccionar_archivo)


def nuevo_archivo():
    nombre = simpledialog.askstring("Nuevo archivo", "Nombre del archivo (sin .txt):")
    if not nombre:
        return
    nombre = nombre.strip()
    # Si el usuario ya escribió ".txt", se lo quitamos para no duplicarlo
    if nombre.lower().endswith(".txt"):
        nombre = nombre[:-4].strip()
    if not nombre:
        return
    # En modo Semántico el archivo debe llevar el prefijo para que aparezca en la lista
    if modo_var.get() == "Semántico" and not es_archivo_semantico(nombre):
        nombre = f"{PREFIJO_SEMANTICO} {nombre}"
    nombre += ".txt"
    ruta = os.path.join(CARPETA, nombre)
    if os.path.exists(ruta):
        messagebox.showerror("Error", "Ya existe un archivo con ese nombre.")
        return
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("")
    texto_entrada.delete("1.0", tk.END)
    archivo_actual["nombre"] = nombre
    archivos_extra.add(nombre)
    cargar_lista()
    ventana.title(f"Analizador - {nombre}")


def eliminar_archivo():
    seleccion = lista_archivos.curselection()
    if not seleccion:
        messagebox.showwarning("Atención", "Selecciona un archivo primero.")
        return
    nombre = lista_archivos.get(seleccion[0])
    if messagebox.askyesno("Confirmar", f"¿Eliminar {nombre}?"):
        os.remove(os.path.join(CARPETA, nombre))
        archivos_extra.discard(nombre)
        if archivo_actual["nombre"] == nombre:
            texto_entrada.delete("1.0", tk.END)
            archivo_actual["nombre"] = None
            ventana.title(TITULO_BASE)
        cargar_lista()


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


def abrir_archivo():
    """Abre un .txt de cualquier lugar. Se copia a la carpeta de trabajo
    y queda en la lista de la izquierda."""
    ruta = filedialog.askopenfilename(
        title="Abrir archivo",
        initialdir=CARPETA,
        filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
    )
    if not ruta:
        return

    nombre = os.path.basename(ruta)
    destino = os.path.join(CARPETA, nombre)

    # Si el archivo viene de otra carpeta, se copia a la carpeta de trabajo
    misma_carpeta = os.path.normcase(os.path.abspath(os.path.dirname(ruta))) == \
        os.path.normcase(os.path.abspath(CARPETA))
    if not misma_carpeta:
        if os.path.exists(destino):
            if not messagebox.askyesno(
                "Archivo existente",
                f"Ya hay un archivo llamado '{nombre}' en la carpeta de trabajo.\n"
                "¿Reemplazarlo con el que acabas de elegir?"
            ):
                return
        shutil.copy2(ruta, destino)

    with open(destino, "r", encoding="utf-8") as f:
        contenido = f.read()
    texto_entrada.delete("1.0", tk.END)
    texto_entrada.insert(tk.END, contenido)
    archivo_actual["nombre"] = nombre
    archivos_extra.add(nombre)
    cargar_lista()
    ventana.title(f"Analizador - {nombre}")


botones_frame = tk.Frame(panel_izquierdo)
botones_frame.pack(pady=5, fill="x")

tk.Button(botones_frame, text="Nuevo", command=nuevo_archivo).pack(side="left", expand=True, fill="x")
tk.Button(botones_frame, text="Abrir...", command=abrir_archivo).pack(side="left", expand=True, fill="x")
tk.Button(botones_frame, text="Eliminar", command=eliminar_archivo).pack(side="left", expand=True, fill="x")

# ---------------- Panel derecho: editor + tabla de tokens ----------------
panel_derecho = tk.Frame(ventana)
panel_derecho.pack(side="left", fill="both", expand=True, padx=10, pady=10)

# --- Selector de modo de análisis ---
modo_frame = tk.Frame(panel_derecho)
modo_frame.pack(fill="x", pady=(0, 8))

tk.Label(modo_frame, text="Analizador:").pack(side="left")

modo_var = tk.StringVar(value="Léxico")
combo_modo = ttk.Combobox(
    modo_frame,
    textvariable=modo_var,
    values=["Léxico", "Sintáctico", "Semántico", "Traductor"],
    state="readonly",
    width=15
)
combo_modo.pack(side="left", padx=5)

# --- Selector de lenguaje destino (solo visible en modo Traductor) ---
destino_frame = tk.Frame(modo_frame)
tk.Label(destino_frame, text="Traducir a:").pack(side="left")

destino_var = tk.StringVar(value=DESTINOS[0])
combo_destino = ttk.Combobox(
    destino_frame,
    textvariable=destino_var,
    values=DESTINOS,
    state="readonly",
    width=26
)
combo_destino.pack(side="left", padx=5)


def titulo_resultado():
    modo = modo_var.get()
    if modo == "Traductor":
        return "Resultado de la traducción:"
    return f"Resultado del análisis {modo.lower()}:"


def actualizar_controles_traductor():
    """Muestra u oculta el selector de destino y el botón de guardar traducción."""
    if modo_var.get() == "Traductor":
        destino_frame.pack(side="left", padx=(15, 0))
        boton_guardar_traduccion.pack(side="left", padx=5)
    else:
        destino_frame.pack_forget()
        boton_guardar_traduccion.pack_forget()


def al_cambiar_modo(event=None):
    # Si hay un archivo abierto, se guarda y se mantiene visible y en el editor
    if archivo_actual["nombre"]:
        guardar_archivo(mostrar_aviso=False)
        archivos_extra.add(archivo_actual["nombre"])
    cargar_lista()
    etiqueta_resultado.config(text=titulo_resultado())
    actualizar_controles_traductor()


def al_cambiar_destino(event=None):
    # Si ya hay un archivo abierto, se vuelve a traducir con el nuevo destino
    if modo_var.get() == "Traductor" and archivo_actual["nombre"]:
        analizar()


combo_modo.bind("<<ComboboxSelected>>", al_cambiar_modo)
combo_destino.bind("<<ComboboxSelected>>", al_cambiar_destino)

tk.Label(panel_derecho, text="Contenido del archivo:").pack(anchor="w")

texto_entrada = tk.Text(panel_derecho, height=10)
texto_entrada.pack(fill="both", expand=True)

acciones_frame = tk.Frame(panel_derecho)
acciones_frame.pack(fill="x", pady=5)

tk.Button(acciones_frame, text="Guardar", command=guardar_archivo).pack(side="left", padx=5)


def escribir(texto):
    texto_resultado.insert(tk.END, texto)


def guardar_traduccion():
    """Guarda el último código traducido con la extensión del lenguaje destino."""
    if not ultima_traduccion["codigo"]:
        messagebox.showwarning(
            "Atención",
            "Todavía no hay una traducción. Pulsa 'Analizar' en modo Traductor primero."
        )
        return
    destino = ultima_traduccion["destino"]
    extension = EXTENSIONES[destino]
    base = os.path.splitext(archivo_actual["nombre"] or "traduccion")[0]
    ruta = filedialog.asksaveasfilename(
        title=f"Guardar traducción a {destino}",
        initialdir=CARPETA,
        initialfile=base + extension,
        defaultextension=extension,
        filetypes=[(f"Archivos {extension}", f"*{extension}"), ("Todos los archivos", "*.*")]
    )
    if not ruta:
        return
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(ultima_traduccion["codigo"])
    messagebox.showinfo("Guardado", f"Traducción guardada en:\n{ruta}")


def analizar():
    if not archivo_actual["nombre"]:
        messagebox.showwarning("Atención", "Guarda o abre un archivo primero.")
        return
    guardar_archivo(mostrar_aviso=False)
    ruta = os.path.join(CARPETA, archivo_actual["nombre"])

    if not os.path.exists(EJECUTABLE):
        messagebox.showerror("Error", "No se encontró analizador.exe en esta carpeta.")
        return

    # Cada análisis empieza sin traducción previa
    ultima_traduccion["codigo"] = None
    ultima_traduccion["destino"] = None

    # ---------- 1) LÉXICO (siempre se ejecuta) ----------
    resultado = subprocess.run(
        [EJECUTABLE, ruta],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    for fila in tabla_tokens.get_children():
        tabla_tokens.delete(fila)

    hay_error_lexico = False
    for linea in resultado.stdout.splitlines():
        if "\t" in linea:
            tipo, valor = linea.split("\t", 1)
            tabla_tokens.insert("", tk.END, values=(tipo, valor))
            if tipo == "ERROR_LEXICO":
                hay_error_lexico = True

    texto_resultado.config(state="normal")
    texto_resultado.delete("1.0", tk.END)

    modo = modo_var.get()

    if modo == "Léxico":
        escribir(
            "Modo Léxico: solo se muestra la tabla de tokens. "
            "Cambia a 'Sintáctico', 'Semántico' o 'Traductor' en el desplegable para ver más análisis."
        )

    elif modo == "Traductor":
        # ---------- 4) TRADUCTOR ----------
        destino = destino_var.get()
        if hay_error_lexico:
            escribir(
                "No se puede traducir: hay errores léxicos en el archivo. "
                "Corrígelos primero.\n"
            )
        else:
            try:
                codigo, arbol = traducir(resultado.stdout, destino)
            except ErrorTraduccion as e:
                escribir("--- Resultado ---\n")
                escribir(f"ERROR DE TRADUCCIÓN: {e}\n")
            else:
                ultima_traduccion["codigo"] = codigo
                ultima_traduccion["destino"] = destino
                escribir("--- Árbol sintáctico (AST) ---\n")
                escribir(arbol.rstrip("\n") + "\n")
                escribir(f"\n--- Código traducido a {destino} ---\n")
                escribir(codigo)
                escribir("\n--- Resultado ---\n")
                escribir(f"TRADUCCIÓN CORRECTA a {destino}. "
                         "Usa 'Guardar traducción' para guardar el código.\n")

    else:
        # Sintáctico y Semántico necesitan que no haya errores léxicos
        if hay_error_lexico:
            escribir(
                f"No se puede hacer el análisis {modo.lower()}: "
                "hay errores léxicos en el archivo. Corrígelos primero.\n"
            )
        else:
            tokens = tokens_desde_salida(resultado.stdout)

            # ---------- 2) SINTÁCTICO ----------
            aceptado, log, error = analizar_sintaxis(tokens)

            if modo == "Sintáctico":
                escribir("--- Derivación paso a paso ---\n")
                for paso in log:
                    escribir(paso + "\n")
                escribir("\n--- Resultado ---\n")
                if aceptado:
                    escribir("Cadena ACEPTADA (sintaxis correcta)\n")
                else:
                    escribir(f"ERROR DE SINTAXIS: {error}\n")

            # ---------- 3) SEMÁNTICO ----------
            else:
                if not aceptado:
                    escribir("No se puede hacer el análisis semántico: hay un error de sintaxis.\n")
                    escribir(f"ERROR DE SINTAXIS: {error}\n")
                else:
                    ok, log_sem, errores, historial = analizar_semantica(tokens)

                    escribir("--- Tabla de símbolos ---\n")
                    if historial:
                        escribir(f"{'Nombre':<15}{'Tipo':<12}{'Ámbito'}\n")
                        for nombre, tipo, nivel in historial:
                            etiqueta = "global" if nivel == 0 else f"bloque {nivel}"
                            escribir(f"{nombre:<15}{tipo:<12}{etiqueta}\n")
                    else:
                        escribir("(vacía)\n")

                    escribir("\n--- Comprobaciones realizadas ---\n")
                    for paso in log_sem:
                        escribir(paso + "\n")

                    escribir("\n--- Resultado ---\n")
                    if ok:
                        escribir("ANÁLISIS SEMÁNTICO CORRECTO\n")
                    else:
                        escribir(f"Se encontraron {len(errores)} error(es) semántico(s):\n")
                        for e in errores:
                            escribir(f"  • {e}\n")

    texto_resultado.config(state="disabled")


tk.Button(acciones_frame, text="Analizar", command=analizar, bg="#00b894", fg="white").pack(side="left", padx=5)

# Botón de guardar traducción: se muestra solo en modo Traductor (ver actualizar_controles_traductor)
boton_guardar_traduccion = tk.Button(
    acciones_frame, text="Guardar traducción", command=guardar_traduccion,
    bg="#0984e3", fg="white"
)

tk.Label(panel_derecho, text="Tokens generados:").pack(anchor="w", pady=(10, 0))

tabla_tokens = ttk.Treeview(panel_derecho, columns=("tipo", "valor"), show="headings", height=8)
tabla_tokens.heading("tipo", text="Tipo de Token")
tabla_tokens.heading("valor", text="Valor")
tabla_tokens.column("tipo", width=200)
tabla_tokens.column("valor", width=400)
tabla_tokens.pack(fill="both", expand=True)

etiqueta_resultado = tk.Label(panel_derecho, text="Resultado del análisis léxico:")
etiqueta_resultado.pack(anchor="w", pady=(10, 0))

texto_resultado = tk.Text(panel_derecho, height=10, state="disabled")
texto_resultado.pack(fill="both", expand=True)

cargar_lista()

ventana.mainloop()