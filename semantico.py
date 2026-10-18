# semantico.py
# Analizador semántico: tabla de símbolos, ámbitos y comprobación de tipos.
# Se ejecuta DESPUÉS del sintáctico, sobre la misma lista de tokens.

OPS_ARITMETICOS_1 = ("+", "-")
OPS_ARITMETICOS_2 = ("*", "/", "%")
TIPOS_NUMERICOS = ("entero", "decimal")
TIPOS_DECLARABLES = ("entero", "decimal", "texto")


class TablaSimbolos:
    """Pila de ámbitos. Cada ámbito es un diccionario nombre -> tipo."""

    def __init__(self):
        self.ambitos = [{}]      # el primero es el ámbito global
        self.historial = []      # (nombre, tipo, nivel) para mostrarlo en la interfaz

    def entrar_ambito(self):
        self.ambitos.append({})

    def salir_ambito(self):
        self.ambitos.pop()

    def declarar(self, nombre, tipo):
        if nombre in self.ambitos[-1]:
            return False
        self.ambitos[-1][nombre] = tipo
        self.historial.append((nombre, tipo, len(self.ambitos) - 1))
        return True

    def buscar(self, nombre):
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                return ambito[nombre]
        return None


def compatible(destino, origen):
    """¿Se puede guardar un valor de tipo 'origen' en una variable 'destino'?"""
    if origen == "error" or destino == "error":
        return True             
    if destino == origen:
        return True
    return destino == "decimal" and origen == "entero"


def resultado_aritmetico(op, a, b):
    """Tipo que resulta de aplicar un operador aritmético, o None si no es válido."""
    if a == "error" or b == "error":
        return "error"
    if op == "+" and a == "texto" and b == "texto":
        return "texto"
    if a in TIPOS_NUMERICOS and b in TIPOS_NUMERICOS:
        return "decimal" if "decimal" in (a, b) else "entero"
    return None


class AnalizadorSemantico:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.tabla = TablaSimbolos()
        self.errores = []
        self.log = []
        self.inicio = 1          # número del primer token de la instrucción actual

    # ---------- utilidades ----------
    def actual(self):
        return self.tokens[self.pos]

    def avanzar(self):
        tok = self.tokens[self.pos]
        if tok[0] != "$":
            self.pos += 1
        return tok

    def es(self, valor):
        tipo, v = self.actual()
        return v == valor and tipo != "CADENA"

    def error(self, mensaje):
        self.errores.append(f"{mensaje} (instrucción que empieza en el token #{self.inicio})")

    # ---------- estructura ----------
    def programa(self):
        while self.actual()[0] != "$":
            self.instr()

    def instr(self):
        tipo, valor = self.actual()
        self.inicio = self.pos + 1
        if tipo == "PALABRA_CLAVE" and valor in TIPOS_DECLARABLES:
            self.declaracion()
        elif tipo == "PALABRA_CLAVE" and valor == "si":
            self.si_instr()
        elif tipo == "PALABRA_CLAVE" and valor == "mientras":
            self.mientras_instr()
        elif tipo == "PALABRA_CLAVE" and valor == "retorno":
            self.retorno_instr()
        elif valor == "imprimir" and tipo in ("ID", "PALABRA_CLAVE"):
            self.imprimir_instr()
        elif tipo == "ID":
            self.asignacion()
        else:
            self.avanzar()       # token inesperado: avanzar para no quedar en ciclo

    def bloque(self):
        self.avanzar()                       # {
        self.tabla.entrar_ambito()
        self.log.append("se abre un nuevo ámbito")
        while not self.es("}") and self.actual()[0] != "$":
            self.instr()
        self.avanzar()                       # }
        self.tabla.salir_ambito()
        self.log.append("se cierra el ámbito")

    # ---------- instrucciones ----------
    def declaracion(self):
        tipo_dec = self.avanzar()[1]
        nombre = self.avanzar()[1]
        self.avanzar()                       # =
        tipo_expr = self.expr()
        self.avanzar()                       # ;
        if not compatible(tipo_dec, tipo_expr):
            self.error(f"No se puede asignar un valor '{tipo_expr}' a '{nombre}' de tipo '{tipo_dec}'")
        if self.tabla.declarar(nombre, tipo_dec):
            nivel = len(self.tabla.ambitos) - 1
            self.log.append(f"declaración: {nombre} : {tipo_dec} (ámbito {nivel})")
        else:
            self.error(f"La variable '{nombre}' ya fue declarada en este ámbito")

    def asignacion(self):
        nombre = self.avanzar()[1]
        tipo_var = self.tabla.buscar(nombre)
        self.avanzar()                       # =
        tipo_expr = self.expr()
        self.avanzar()                       # ;
        if tipo_var is None:
            self.error(f"La variable '{nombre}' no ha sido declarada")
        elif not compatible(tipo_var, tipo_expr):
            self.error(f"No se puede asignar un valor '{tipo_expr}' a '{nombre}' de tipo '{tipo_var}'")
        else:
            self.log.append(f"asignación: {nombre} ({tipo_var}) = valor '{tipo_expr}'")

    def condicion(self, nombre, tipo):
        if tipo not in ("booleano", "error"):
            self.error(f"La condición del '{nombre}' debe ser booleana, pero es '{tipo}'")
        else:
            self.log.append(f"condición de '{nombre}': {tipo}")

    def si_instr(self):
        self.avanzar()                       # si
        self.avanzar()                       # (
        tipo = self.expr()
        self.avanzar()                       # )
        self.condicion("si", tipo)
        self.bloque()
        if self.actual() == ("PALABRA_CLAVE", "sino"):
            self.avanzar()
            self.bloque()

    def mientras_instr(self):
        self.avanzar()                       # mientras
        self.avanzar()                       # (
        tipo = self.expr()
        self.avanzar()                       # )
        self.condicion("mientras", tipo)
        self.bloque()

    def retorno_instr(self):
        self.avanzar()                       # retorno
        tipo = self.expr()
        self.avanzar()                       # ;
        self.log.append(f"retorno de un valor '{tipo}'")

    def imprimir_instr(self):
        self.avanzar()                       # imprimir
        self.avanzar()                       # (
        tipo = self.expr()
        self.avanzar()                       # )
        self.avanzar()                       # ;
        self.log.append(f"imprimir un valor '{tipo}'")

    # ---------- expresiones: cada una DEVUELVE su tipo ----------
    def expr(self):
        tipo = self.exprAnd()
        while self.es("O"):
            self.avanzar()
            otro = self.exprAnd()
            if tipo != "error" and otro != "error" and (tipo != "booleano" or otro != "booleano"):
                self.error(f"El operador 'O' necesita valores booleanos, no '{tipo}' y '{otro}'")
            tipo = "booleano"
        return tipo

    def exprAnd(self):
        tipo = self.exprRel()
        while self.es("Y"):
            self.avanzar()
            otro = self.exprRel()
            if tipo != "error" and otro != "error" and (tipo != "booleano" or otro != "booleano"):
                self.error(f"El operador 'Y' necesita valores booleanos, no '{tipo}' y '{otro}'")
            tipo = "booleano"
        return tipo

    def exprRel(self):
        tipo = self.exprAr()
        if self.actual()[0] == "OPREL":
            op = self.avanzar()[1]
            otro = self.exprAr()
            if tipo != "error" and otro != "error":
                ambos_num = tipo in TIPOS_NUMERICOS and otro in TIPOS_NUMERICOS
                ambos_txt = tipo == "texto" and otro == "texto"
                if not (ambos_num or ambos_txt):
                    self.error(f"No se pueden comparar '{tipo}' y '{otro}' con '{op}'")
            return "booleano"
        return tipo

    def exprAr(self):
        tipo = self.term()
        while self.actual()[1] in OPS_ARITMETICOS_1 and self.actual()[0] == "OP_ARITMETICO":
            op = self.avanzar()[1]
            otro = self.term()
            tipo = self.aplicar(op, tipo, otro)
        return tipo

    def term(self):
        tipo = self.factor()
        while self.actual()[1] in OPS_ARITMETICOS_2 and self.actual()[0] == "OP_ARITMETICO":
            op = self.avanzar()[1]
            otro = self.factor()
            tipo = self.aplicar(op, tipo, otro)
        return tipo

    def aplicar(self, op, a, b):
        resultado = resultado_aritmetico(op, a, b)
        if resultado is None:
            self.error(f"No se puede aplicar '{op}' entre '{a}' y '{b}'")
            return "error"
        return resultado

    def factor(self):
        tipo, valor = self.actual()
        if tipo == "NUMERO_ENTERO":
            self.avanzar()
            return "entero"
        if tipo == "NUMERO_DECIMAL":
            self.avanzar()
            return "decimal"
        if tipo == "CADENA":
            self.avanzar()
            return "texto"
        if tipo == "ID":
            self.avanzar()
            t = self.tabla.buscar(valor)
            if t is None:
                self.error(f"La variable '{valor}' no ha sido declarada")
                return "error"
            return t
        if self.es("("):
            self.avanzar()
            t = self.expr()
            self.avanzar()                   # )
            return t
        self.avanzar()
        return "error"


def analizar_semantica(tokens):
    """Devuelve (correcto, log, errores, tabla_de_simbolos)."""
    a = AnalizadorSemantico(tokens)
    try:
        a.programa()
    except Exception as e:
        a.errores.append(f"Error interno del analizador semántico: {e}")
    return (len(a.errores) == 0, a.log, a.errores, a.tabla.historial)