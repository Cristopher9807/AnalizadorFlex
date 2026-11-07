"""
traductor.py
------------
Traductor de código del lenguaje del proyecto (Flex + Python) hacia otros
lenguajes. Está construido sobre lo que ya existe:

    analizador.exe (Flex)  ->  tokens "TIPO<TAB>valor"
    traductor.py           ->  parser que construye un AST (árbol sintáctico)
                               + comprobación de tipos + generadores de código

Destinos disponibles:
    - Python
    - JavaScript
    - C++
    - Código de tres direcciones (representación intermedia del capítulo 6)

Estructura (igual que un compilador real):
    front-end : leer_tokens -> construir_ast   (análisis + tipos)
    back-end  : generar(ast, destino)          (un generador por lenguaje)
"""

import keyword
import json

# ----------------------------------------------------------------------------
# Constantes públicas
# ----------------------------------------------------------------------------
DESTINOS = ["Python", "JavaScript", "C++", "Código de tres direcciones"]

EXTENSIONES = {
    "Python": ".py",
    "JavaScript": ".js",
    "C++": ".cpp",
    "Código de tres direcciones": ".tac",
}


class ErrorTraduccion(Exception):
    """Error léxico, sintáctico o de tipos detectado al traducir."""


# ----------------------------------------------------------------------------
# 1. Tokens (salida de analizador.exe)
# ----------------------------------------------------------------------------
def leer_tokens(salida):
    """Convierte la salida del ejecutable (líneas TIPO<TAB>valor) en una lista
    de tuplas (tipo, valor)."""
    tokens = []
    for linea in salida.splitlines():
        if "\t" in linea:
            tipo, valor = linea.split("\t", 1)
            tokens.append((tipo.strip(), valor.rstrip("\r")))
    return tokens


# ----------------------------------------------------------------------------
# 2. Nodos del AST
# ----------------------------------------------------------------------------
class Nodo:
    pass


class Programa(Nodo):
    def __init__(self, instrucciones):
        self.instrucciones = instrucciones


class Declaracion(Nodo):
    def __init__(self, tipo, nombre, expr):
        self.tipo, self.nombre, self.expr = tipo, nombre, expr


class Asignacion(Nodo):
    def __init__(self, nombre, tipo, expr):
        self.nombre, self.tipo, self.expr = nombre, tipo, expr


class Si(Nodo):
    def __init__(self, condicion, bloque, sino):
        self.condicion, self.bloque, self.sino = condicion, bloque, sino


class Mientras(Nodo):
    def __init__(self, condicion, bloque):
        self.condicion, self.bloque = condicion, bloque


class Retorno(Nodo):
    def __init__(self, expr):
        self.expr = expr


class Comentario(Nodo):
    def __init__(self, texto):
        self.texto = texto


class Binaria(Nodo):
    def __init__(self, op, izq, der, tipo):
        self.op, self.izq, self.der, self.tipo = op, izq, der, tipo


class Numero(Nodo):
    def __init__(self, valor, tipo):
        self.valor, self.tipo = valor, tipo


class Cadena(Nodo):
    def __init__(self, valor):
        self.valor, self.tipo = valor, "texto"


class Variable(Nodo):
    def __init__(self, nombre, tipo):
        self.nombre, self.tipo = nombre, tipo


# Precedencia de los operadores del lenguaje fuente (mayor = se evalúa antes)
PREC = {
    "O": 1, "Y": 2,
    "<": 3, "<=": 3, ">": 3, ">=": 3, "==": 3, "!=": 3,
    "+": 4, "-": 4,
    "*": 5, "/": 5, "%": 5,
}
OPS_REL = {"<", "<=", ">", ">=", "==", "!="}
TIPOS_NUM = ("entero", "decimal")


# ----------------------------------------------------------------------------
# 3. Parser (descenso recursivo) + comprobación de tipos
# ----------------------------------------------------------------------------
class _Parser:
    def __init__(self, tokens):
        self.t = tokens
        self.i = 0
        self.ambitos = [{}]          # pila de tablas de símbolos

    # ---- utilidades de lectura ----
    def _mirar(self, comentarios=False):
        if not comentarios:
            while self.i < len(self.t) and self.t[self.i][0] == "COMENTARIO":
                self.i += 1
        if self.i < len(self.t):
            return self.t[self.i]
        return ("EOF", "")

    def _tomar(self, comentarios=False):
        tok = self._mirar(comentarios)
        self.i += 1
        return tok

    def _es(self, tok, tipo, valor=None):
        return tok[0] == tipo and (valor is None or tok[1] == valor)

    def _esperar(self, tipo, valor, descripcion):
        tok = self._tomar()
        if not self._es(tok, tipo, valor):
            encontrado = tok[1] if tok[0] != "EOF" else "fin del archivo"
            raise ErrorTraduccion(
                f"Error de sintaxis: se esperaba {descripcion} y se encontró '{encontrado}'."
            )
        return tok

    # ---- tabla de símbolos ----
    def _declarar(self, nombre, tipo):
        if nombre in self.ambitos[-1]:
            raise ErrorTraduccion(f"Error semántico: la variable '{nombre}' ya fue declarada en este ámbito.")
        self.ambitos[-1][nombre] = tipo

    def _buscar(self, nombre):
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                return ambito[nombre]
        raise ErrorTraduccion(f"Error semántico: la variable '{nombre}' no ha sido declarada.")

    # ---- programa e instrucciones ----
    def programa(self):
        instrucciones = []
        while self._mirar(True)[0] != "EOF":
            instrucciones.append(self.instruccion())
        return Programa(instrucciones)

    def instruccion(self):
        tok = self._mirar(True)
        tipo, valor = tok
        if tipo == "COMENTARIO":
            self._tomar(True)
            return Comentario(valor[2:].rstrip() if valor.startswith("//") else valor)
        if tipo == "PALABRA_CLAVE" and valor in ("entero", "decimal", "texto"):
            return self.declaracion()
        if tipo == "PALABRA_CLAVE" and valor == "si":
            return self.si()
        if tipo == "PALABRA_CLAVE" and valor == "mientras":
            return self.mientras()
        if tipo == "PALABRA_CLAVE" and valor == "retorno":
            return self.retorno()
        if tipo == "ID":
            return self.asignacion()
        encontrado = valor if tipo != "EOF" else "fin del archivo"
        raise ErrorTraduccion(f"Error de sintaxis: instrucción inesperada '{encontrado}'.")

    def declaracion(self):
        tipo = self._tomar()[1]
        nombre = self._esperar_id()
        self._esperar("PUNTUACION", "=", "'='")
        expr = self.expr()
        self._esperar("PUNTUACION", ";", "';'")
        self._comprobar_asignacion(nombre, tipo, expr.tipo)
        self._declarar(nombre, tipo)
        return Declaracion(tipo, nombre, expr)

    def asignacion(self):
        nombre = self._tomar()[1]
        tipo = self._buscar(nombre)
        self._esperar("PUNTUACION", "=", "'='")
        expr = self.expr()
        self._esperar("PUNTUACION", ";", "';'")
        self._comprobar_asignacion(nombre, tipo, expr.tipo)
        return Asignacion(nombre, tipo, expr)

    def si(self):
        self._tomar()
        self._esperar("PUNTUACION", "(", "'('")
        cond = self.expr()
        self._comprobar_condicion(cond)
        self._esperar("PUNTUACION", ")", "')'")
        bloque = self.bloque()
        sino = None
        sig = self._mirar()
        if self._es(sig, "PALABRA_CLAVE", "sino"):
            self._tomar()
            sino = self.bloque()
        return Si(cond, bloque, sino)

    def mientras(self):
        self._tomar()
        self._esperar("PUNTUACION", "(", "'('")
        cond = self.expr()
        self._comprobar_condicion(cond)
        self._esperar("PUNTUACION", ")", "')'")
        return Mientras(cond, self.bloque())

    def retorno(self):
        self._tomar()
        expr = self.expr()
        self._esperar("PUNTUACION", ";", "';'")
        return Retorno(expr)

    def bloque(self):
        self._esperar("PUNTUACION", "{", "'{'")
        self.ambitos.append({})
        instrucciones = []
        while True:
            tok = self._mirar(True)
            if self._es(tok, "PUNTUACION", "}"):
                self._tomar(True)
                break
            if tok[0] == "EOF":
                raise ErrorTraduccion("Error de sintaxis: falta cerrar un bloque con '}'.")
            instrucciones.append(self.instruccion())
        self.ambitos.pop()
        return instrucciones

    def _esperar_id(self):
        tok = self._tomar()
        if tok[0] != "ID":
            encontrado = tok[1] if tok[0] != "EOF" else "fin del archivo"
            raise ErrorTraduccion(f"Error de sintaxis: se esperaba un identificador y se encontró '{encontrado}'.")
        return tok[1]

    # ---- expresiones (misma precedencia que parser.py) ----
    def expr(self):
        izq = self.expr_and()
        while self._es(self._mirar(), "OP_LOGICO", "O"):
            self._tomar()
            der = self.expr_and()
            izq = self._binaria("O", izq, der)
        return izq

    def expr_and(self):
        izq = self.expr_rel()
        while self._es(self._mirar(), "OP_LOGICO", "Y"):
            self._tomar()
            der = self.expr_rel()
            izq = self._binaria("Y", izq, der)
        return izq

    def expr_rel(self):
        izq = self.expr_ar()
        tok = self._mirar()
        if tok[0] == "OPREL":
            self._tomar()
            der = self.expr_ar()
            return self._binaria(tok[1], izq, der)
        return izq

    def expr_ar(self):
        izq = self.termino()
        while True:
            tok = self._mirar()
            if tok[0] == "OP_ARITMETICO" and tok[1] in ("+", "-"):
                self._tomar()
                izq = self._binaria(tok[1], izq, self.termino())
            else:
                return izq

    def termino(self):
        izq = self.factor()
        while True:
            tok = self._mirar()
            if tok[0] == "OP_ARITMETICO" and tok[1] in ("*", "/", "%"):
                self._tomar()
                izq = self._binaria(tok[1], izq, self.factor())
            else:
                return izq

    def factor(self):
        tok = self._tomar()
        tipo, valor = tok
        if tipo == "PUNTUACION" and valor == "(":
            e = self.expr()
            self._esperar("PUNTUACION", ")", "')'")
            return e
        if tipo == "ID":
            return Variable(valor, self._buscar(valor))
        if tipo == "NUMERO_ENTERO":
            return Numero(valor, "entero")
        if tipo == "NUMERO_DECIMAL":
            return Numero(valor, "decimal")
        if tipo == "CADENA":
            if len(valor) >= 2 and valor[0] == '"' and valor[-1] == '"':
                valor = valor[1:-1]
            return Cadena(valor)
        encontrado = valor if tipo != "EOF" else "fin del archivo"
        raise ErrorTraduccion(f"Error de sintaxis: se esperaba un valor (id, número, cadena o '(') y se encontró '{encontrado}'.")

    # ---- reglas de tipos ----
    def _binaria(self, op, izq, der):
        ti, td = izq.tipo, der.tipo
        if op in ("Y", "O"):
            if ti == "texto" or td == "texto":
                raise ErrorTraduccion(f"Error de tipos: el operador '{op}' no acepta texto.")
            tipo = "logico"
        elif op in OPS_REL:
            if (ti == "texto") != (td == "texto"):
                raise ErrorTraduccion(f"Error de tipos: no se puede comparar {ti} con {td}.")
            tipo = "logico"
        elif op == "+" and ti == "texto" and td == "texto":
            tipo = "texto"
        else:
            if ti not in TIPOS_NUM or td not in TIPOS_NUM:
                raise ErrorTraduccion(f"Error de tipos: el operador '{op}' no se puede aplicar a {ti} y {td}.")
            if op == "%" and (ti != "entero" or td != "entero"):
                raise ErrorTraduccion("Error de tipos: el operador '%' solo acepta enteros.")
            tipo = "decimal" if "decimal" in (ti, td) else "entero"
        return Binaria(op, izq, der, tipo)

    def _comprobar_asignacion(self, nombre, destino, origen):
        ok = (destino == origen) or (destino == "decimal" and origen == "entero")
        if not ok:
            raise ErrorTraduccion(f"Error de tipos: no se puede asignar {origen} a '{nombre}' (que es {destino}).")

    def _comprobar_condicion(self, cond):
        if cond.tipo == "texto":
            raise ErrorTraduccion("Error de tipos: la condición no puede ser de tipo texto.")


def construir_ast(tokens):
    """Front-end: tokens -> AST. Lanza ErrorTraduccion si hay errores."""
    for tipo, valor in tokens:
        if tipo == "ERROR_LEXICO":
            raise ErrorTraduccion(f"Error léxico: {valor}. Corrígelo antes de traducir.")
    if not tokens:
        raise ErrorTraduccion("El archivo está vacío: no hay nada que traducir.")
    return _Parser(tokens).programa()


# ----------------------------------------------------------------------------
# 4. Utilidades comunes de los generadores
# ----------------------------------------------------------------------------
_RESERVADAS = {
    "Python": set(keyword.kwlist) | {"main", "int", "str", "float", "print", "len", "input"},
    "JavaScript": {
        "break", "case", "catch", "class", "const", "continue", "debugger", "default", "delete",
        "do", "else", "enum", "export", "extends", "false", "finally", "for", "function", "if",
        "import", "in", "instanceof", "new", "null", "return", "super", "switch", "this", "throw",
        "true", "try", "typeof", "var", "void", "while", "with", "yield", "let", "static",
        "await", "async", "of", "undefined", "NaN", "Infinity", "Math", "main", "console",
    },
    "C++": {
        "alignas", "alignof", "and", "and_eq", "asm", "auto", "bitand", "bitor", "bool", "break",
        "case", "catch", "char", "class", "compl", "const", "constexpr", "continue", "decltype",
        "default", "delete", "do", "double", "else", "enum", "explicit", "export", "extern",
        "false", "float", "for", "friend", "goto", "if", "inline", "int", "long", "main",
        "mutable", "namespace", "new", "noexcept", "not", "not_eq", "nullptr", "operator", "or",
        "or_eq", "private", "protected", "public", "register", "return", "short", "signed",
        "sizeof", "static", "struct", "switch", "template", "this", "throw", "true", "try",
        "typedef", "typeid", "typename", "union", "unsigned", "using", "virtual", "void",
        "volatile", "while", "xor", "xor_eq", "std",
    },
}


def _nombre(nombre, destino):
    """Evita choques con palabras reservadas del lenguaje destino."""
    if destino in _RESERVADAS and nombre in _RESERVADAS[destino]:
        return nombre + "_"
    return nombre


def _necesita_paren(hijo, op_padre, es_derecho):
    if not isinstance(hijo, Binaria):
        return False
    p_hijo, p_padre = PREC[hijo.op], PREC[op_padre]
    if p_hijo < p_padre:
        return True
    if p_hijo == p_padre and (es_derecho or p_padre == 3):
        return True
    return False


def _literal_cadena(valor, destino):
    if destino == "C++":
        escapado = valor.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
        return '"' + escapado + '"'
    return json.dumps(valor, ensure_ascii=False)


# ----------------------------------------------------------------------------
# 5. Generadores: Python, JavaScript, C++
# ----------------------------------------------------------------------------
_OPS = {
    "Python": {"Y": "and", "O": "or"},
    "JavaScript": {"Y": "&&", "O": "||", "==": "===", "!=": "!=="},
    "C++": {"Y": "&&", "O": "||"},
}


def _expr(e, destino, op_padre=None, es_derecho=False):
    if isinstance(e, Numero):
        return e.valor
    if isinstance(e, Variable):
        return _nombre(e.nombre, destino)
    if isinstance(e, Cadena):
        return _literal_cadena(e.valor, destino)

    # Binaria
    izq = _expr(e.izq, destino, e.op, False)
    der = _expr(e.der, destino, e.op, True)

    # Los literales de texto en C++ deben convertirse a std::string para poder sumarse
    if destino == "C++" and e.op == "+" and e.tipo == "texto":
        if isinstance(e.izq, Cadena):
            izq = f"std::string({izq})"
        if isinstance(e.der, Cadena):
            der = f"std::string({der})"

    if _necesita_paren(e.izq, e.op, False):
        izq = f"({izq})"
    if _necesita_paren(e.der, e.op, True):
        der = f"({der})"

    # División entera: en el lenguaje fuente entero / entero es entero
    if e.op == "/" and e.izq.tipo == "entero" and e.der.tipo == "entero":
        if destino == "Python":
            return f"int({izq} / {der})"
        if destino == "JavaScript":
            return f"Math.trunc({izq} / {der})"

    op = _OPS[destino].get(e.op, e.op)
    return f"{izq} {op} {der}"


def _expr_sin_paren_externa(e, destino):
    """Expresión usada como condición/valor completo (sin padre)."""
    return _expr(e, destino)


def _tipo_cpp(tipo):
    return {"entero": "int", "decimal": "double", "texto": "std::string"}[tipo]


def _generar_python(prog):
    lineas = ["# Código generado por el traductor (destino: Python)", "", "def main():"]

    def bloque(instrucciones, nivel):
        for ins in instrucciones:
            instruccion(ins, nivel)
        # Python no admite bloques vacíos (ni con solo comentarios): hace falta 'pass'
        if all(isinstance(i, Comentario) for i in instrucciones):
            lineas.append("    " * nivel + "pass")

    def instruccion(n, nivel):
        sangria = "    " * nivel
        if isinstance(n, Comentario):
            lineas.append(f"{sangria}# {n.texto.strip()}".rstrip())
        elif isinstance(n, (Declaracion, Asignacion)):
            valor = _expr(n.expr, 'Python')
            # entero asignado a decimal: en Python hay que convertirlo a float
            if n.tipo == "decimal" and n.expr.tipo == "entero":
                valor = f"float({valor})"
            lineas.append(f"{sangria}{_nombre(n.nombre, 'Python')} = {valor}")
        elif isinstance(n, Si):
            lineas.append(f"{sangria}if {_expr(n.condicion, 'Python')}:")
            bloque(n.bloque, nivel + 1)
            if n.sino is not None:
                lineas.append(f"{sangria}else:")
                bloque(n.sino, nivel + 1)
        elif isinstance(n, Mientras):
            lineas.append(f"{sangria}while {_expr(n.condicion, 'Python')}:")
            bloque(n.bloque, nivel + 1)
        elif isinstance(n, Retorno):
            lineas.append(f"{sangria}return {_expr(n.expr, 'Python')}")

    bloque(prog.instrucciones, 1)
    lineas += ["", 'if __name__ == "__main__":', "    main()"]
    return "\n".join(lineas) + "\n"


def _generar_js(prog):
    lineas = ["// Código generado por el traductor (destino: JavaScript)", "", "function main() {"]

    def bloque(instrucciones, nivel):
        for ins in instrucciones:
            instruccion(ins, nivel)

    def instruccion(n, nivel):
        sangria = "    " * nivel
        if isinstance(n, Comentario):
            lineas.append(f"{sangria}// {n.texto.strip()}".rstrip())
        elif isinstance(n, Declaracion):
            lineas.append(f"{sangria}let {_nombre(n.nombre, 'JavaScript')} = {_expr(n.expr, 'JavaScript')};")
        elif isinstance(n, Asignacion):
            lineas.append(f"{sangria}{_nombre(n.nombre, 'JavaScript')} = {_expr(n.expr, 'JavaScript')};")
        elif isinstance(n, Si):
            lineas.append(f"{sangria}if ({_expr(n.condicion, 'JavaScript')}) {{")
            bloque(n.bloque, nivel + 1)
            if n.sino is not None:
                lineas.append(f"{sangria}}} else {{")
                bloque(n.sino, nivel + 1)
            lineas.append(f"{sangria}}}")
        elif isinstance(n, Mientras):
            lineas.append(f"{sangria}while ({_expr(n.condicion, 'JavaScript')}) {{")
            bloque(n.bloque, nivel + 1)
            lineas.append(f"{sangria}}}")
        elif isinstance(n, Retorno):
            lineas.append(f"{sangria}return {_expr(n.expr, 'JavaScript')};")

    bloque(prog.instrucciones, 1)
    lineas += ["}", "", "main();"]
    return "\n".join(lineas) + "\n"


def _generar_cpp(prog):
    lineas = [
        "// Código generado por el traductor (destino: C++)",
        "#include <iostream>",
        "#include <string>",
        "",
        "int main() {",
    ]

    def bloque(instrucciones, nivel):
        for ins in instrucciones:
            instruccion(ins, nivel)

    def instruccion(n, nivel):
        sangria = "    " * nivel
        if isinstance(n, Comentario):
            lineas.append(f"{sangria}// {n.texto.strip()}".rstrip())
        elif isinstance(n, Declaracion):
            lineas.append(f"{sangria}{_tipo_cpp(n.tipo)} {_nombre(n.nombre, 'C++')} = {_expr(n.expr, 'C++')};")
        elif isinstance(n, Asignacion):
            lineas.append(f"{sangria}{_nombre(n.nombre, 'C++')} = {_expr(n.expr, 'C++')};")
        elif isinstance(n, Si):
            lineas.append(f"{sangria}if ({_expr(n.condicion, 'C++')}) {{")
            bloque(n.bloque, nivel + 1)
            if n.sino is not None:
                lineas.append(f"{sangria}}} else {{")
                bloque(n.sino, nivel + 1)
            lineas.append(f"{sangria}}}")
        elif isinstance(n, Mientras):
            lineas.append(f"{sangria}while ({_expr(n.condicion, 'C++')}) {{")
            bloque(n.bloque, nivel + 1)
            lineas.append(f"{sangria}}}")
        elif isinstance(n, Retorno):
            if n.expr.tipo == "texto":
                raise ErrorTraduccion("No se puede traducir a C++: 'retorno' de un texto (main devuelve int).")
            valor = _expr(n.expr, "C++")
            if n.expr.tipo == "decimal":
                valor = f"(int)({valor})"
            lineas.append(f"{sangria}return {valor};")

    bloque(prog.instrucciones, 1)
    ultimo = [i for i in prog.instrucciones if not isinstance(i, Comentario)]
    if not ultimo or not isinstance(ultimo[-1], Retorno):
        lineas.append("    return 0;")
    lineas.append("}")
    return "\n".join(lineas) + "\n"


# ----------------------------------------------------------------------------
# 6. Generador de código de tres direcciones (capítulo 6)
# ----------------------------------------------------------------------------
class _TresDirecciones:
    """Código intermedio como en la sección 6.2: una operación por instrucción,
    temporales t1, t2..., etiquetas L1, L2... y saltos if / ifFalse / goto.
    Las conversiones de tipo (ampliación int -> float) se hacen explícitas,
    como en la sección 6.5.2."""

    def __init__(self):
        self.lineas = []
        self.n_temp = 0
        self.n_etq = 0

    def temp(self):
        self.n_temp += 1
        return f"t{self.n_temp}"

    def etiqueta(self):
        self.n_etq += 1
        return f"L{self.n_etq}"

    def emitir(self, texto):
        self.lineas.append("    " + texto)

    def poner_etiqueta(self, etq):
        self.lineas.append(f"{etq}:")

    # --- expresiones: devuelven la "dirección" donde queda el valor ---
    def ampliar(self, direccion, de, a):
        if de == "entero" and a == "decimal":
            t = self.temp()
            self.emitir(f"{t} = (float) {direccion}")
            return t
        return direccion

    def _op(self, op):
        return {"Y": "&&", "O": "||"}.get(op, op)

    def expr(self, e, destino=None):
        if isinstance(e, Numero):
            return e.valor
        if isinstance(e, Variable):
            return e.nombre
        if isinstance(e, Cadena):
            return _literal_cadena(e.valor, "Python")
        izq = self.expr(e.izq)
        der = self.expr(e.der)
        if e.op not in OPS_REL and e.op not in ("Y", "O") and e.tipo == "decimal":
            izq = self.ampliar(izq, e.izq.tipo, "decimal")
            der = self.ampliar(der, e.der.tipo, "decimal")
        elif e.op in OPS_REL and "decimal" in (e.izq.tipo, e.der.tipo):
            izq = self.ampliar(izq, e.izq.tipo, "decimal")
            der = self.ampliar(der, e.der.tipo, "decimal")
        res = destino if destino else self.temp()
        self.emitir(f"{res} = {izq} {self._op(e.op)} {der}")
        return res

    def asignar(self, nombre, tipo_destino, e):
        if isinstance(e, Binaria):
            # x = a op b  (sin temporal intermedio ni copia, como se optimiza en 6.2.3)
            if tipo_destino == "decimal" and e.tipo == "entero":
                t = self.expr(e)
                self.emitir(f"{nombre} = (float) {t}")
            else:
                self.expr(e, destino=nombre)
        else:
            valor = self.expr(e)
            valor = self.ampliar(valor, e.tipo, tipo_destino)
            self.emitir(f"{nombre} = {valor}")

    def salto_si_falso(self, cond, etiqueta):
        if isinstance(cond, Binaria) and cond.op in OPS_REL:
            izq = self.expr(cond.izq)
            der = self.expr(cond.der)
            if "decimal" in (cond.izq.tipo, cond.der.tipo):
                izq = self.ampliar(izq, cond.izq.tipo, "decimal")
                der = self.ampliar(der, cond.der.tipo, "decimal")
            self.emitir(f"ifFalse {izq} {cond.op} {der} goto {etiqueta}")
        else:
            c = self.expr(cond)
            self.emitir(f"ifFalse {c} goto {etiqueta}")

    # --- instrucciones ---
    def instruccion(self, n):
        if isinstance(n, Comentario):
            self.lineas.append(f"    // {n.texto.strip()}".rstrip())
        elif isinstance(n, Declaracion):
            self.asignar(n.nombre, n.tipo, n.expr)
        elif isinstance(n, Asignacion):
            self.asignar(n.nombre, n.tipo, n.expr)
        elif isinstance(n, Si):
            if n.sino is None:
                l_fin = self.etiqueta()
                self.salto_si_falso(n.condicion, l_fin)
                self.bloque(n.bloque)
                self.poner_etiqueta(l_fin)
            else:
                l_sino, l_fin = self.etiqueta(), self.etiqueta()
                self.salto_si_falso(n.condicion, l_sino)
                self.bloque(n.bloque)
                self.emitir(f"goto {l_fin}")
                self.poner_etiqueta(l_sino)
                self.bloque(n.sino)
                self.poner_etiqueta(l_fin)
        elif isinstance(n, Mientras):
            l_ini, l_fin = self.etiqueta(), self.etiqueta()
            self.poner_etiqueta(l_ini)
            self.salto_si_falso(n.condicion, l_fin)
            self.bloque(n.bloque)
            self.emitir(f"goto {l_ini}")
            self.poner_etiqueta(l_fin)
        elif isinstance(n, Retorno):
            self.emitir(f"return {self.expr(n.expr)}")

    def bloque(self, instrucciones):
        for ins in instrucciones:
            self.instruccion(ins)


def _generar_tac(prog):
    g = _TresDirecciones()
    g.lineas.append("// Código intermedio de tres direcciones (capítulo 6)")
    for ins in prog.instrucciones:
        g.instruccion(ins)
    return "\n".join(g.lineas) + "\n"


# ----------------------------------------------------------------------------
# 7. API pública
# ----------------------------------------------------------------------------
def generar(prog, destino):
    if destino == "Python":
        return _generar_python(prog)
    if destino == "JavaScript":
        return _generar_js(prog)
    if destino == "C++":
        return _generar_cpp(prog)
    if destino == "Código de tres direcciones":
        return _generar_tac(prog)
    raise ErrorTraduccion(f"Lenguaje destino desconocido: {destino}")


def arbol_texto(prog):
    """Representación legible del AST (para mostrar en la interfaz)."""
    salida = []

    def e(nodo, n):
        s = "  " * n
        if isinstance(nodo, Binaria):
            salida.append(f"{s}Operación '{nodo.op}'  : {nodo.tipo}")
            e(nodo.izq, n + 1)
            e(nodo.der, n + 1)
        elif isinstance(nodo, Numero):
            salida.append(f"{s}Número {nodo.valor}  : {nodo.tipo}")
        elif isinstance(nodo, Cadena):
            salida.append(f"{s}Cadena \"{nodo.valor}\"  : texto")
        elif isinstance(nodo, Variable):
            salida.append(f"{s}Variable {nodo.nombre}  : {nodo.tipo}")

    def inst(nodo, n):
        s = "  " * n
        if isinstance(nodo, Comentario):
            salida.append(f"{s}Comentario //{nodo.texto}")
        elif isinstance(nodo, Declaracion):
            salida.append(f"{s}Declaración {nodo.tipo} {nodo.nombre}")
            e(nodo.expr, n + 1)
        elif isinstance(nodo, Asignacion):
            salida.append(f"{s}Asignación {nodo.nombre}")
            e(nodo.expr, n + 1)
        elif isinstance(nodo, Si):
            salida.append(f"{s}Si")
            salida.append(f"{s}  condición:")
            e(nodo.condicion, n + 2)
            salida.append(f"{s}  entonces:")
            for i in nodo.bloque:
                inst(i, n + 2)
            if nodo.sino is not None:
                salida.append(f"{s}  sino:")
                for i in nodo.sino:
                    inst(i, n + 2)
        elif isinstance(nodo, Mientras):
            salida.append(f"{s}Mientras")
            salida.append(f"{s}  condición:")
            e(nodo.condicion, n + 2)
            salida.append(f"{s}  cuerpo:")
            for i in nodo.bloque:
                inst(i, n + 2)
        elif isinstance(nodo, Retorno):
            salida.append(f"{s}Retorno")
            e(nodo.expr, n + 1)

    salida.append("Programa")
    for i in prog.instrucciones:
        inst(i, 1)
    return "\n".join(salida) + "\n"


def traducir(salida_lexer, destino):
    """Función principal que usa la interfaz.

    salida_lexer : texto que imprime analizador.exe (líneas TIPO<TAB>valor)
    destino      : uno de DESTINOS
    Devuelve (codigo_generado, arbol_en_texto).
    Lanza ErrorTraduccion si hay errores léxicos, de sintaxis o de tipos.
    """
    tokens = leer_tokens(salida_lexer)
    prog = construir_ast(tokens)
    return generar(prog, destino), arbol_texto(prog)


# ----------------------------------------------------------------------------
# 6. Página web para ejecutar el JavaScript traducido
# ----------------------------------------------------------------------------
def generar_html(codigo_js, titulo="Programa traducido"):
    """Envuelve el JavaScript generado en una página HTML.

    La página se ve en blanco (solo tiene un <script>). El resultado del
    programa (el valor del 'retorno') aparece en la consola del navegador (F12),
    y la función main() queda disponible para volver a llamarla a mano.
    """
    # 1) Quitar la llamada final "main();" que trae el JavaScript generado
    cuerpo = codigo_js.rstrip()
    if cuerpo.endswith("main();"):
        cuerpo = cuerpo[: -len("main();")].rstrip()
    # 2) Evitar que un texto del programa que contenga "</script>" rompa la página
    cuerpo = cuerpo.replace("</", "<\\/")
    # 3) Llamar a main() desde la página y mostrar el resultado en la consola
    cuerpo += '\n\nconsole.log("Resultado del programa:", main());'
    titulo = (titulo or "Programa traducido").replace("<", "").replace(">", "")
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{titulo}</title>
</head>
<body>
<!-- Página generada por el traductor. Abre la consola (F12) para ver el resultado. -->
<script>
{cuerpo}
</script>
</body>
</html>
"""