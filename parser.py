def tokens_desde_salida(salida_texto):
    tokens = []
    for linea in salida_texto.splitlines():
        if "\t" in linea:
            tipo, valor = linea.split("\t", 1)
            if tipo == "COMENTARIO":
                continue
            tokens.append((tipo, valor))
    tokens.append(("$", "$"))
    return tokens


class ErrorSintactico(Exception):
    pass


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.log = []

    def token_actual(self):
        return self.tokens[self.pos]

    def coincidir(self, tipo_esperado, valor_esperado=None):
        tipo, valor = self.token_actual()
        if tipo != tipo_esperado or (valor_esperado is not None and valor != valor_esperado):
            esperado = valor_esperado if valor_esperado is not None else tipo_esperado
            raise ErrorSintactico(
                f"Se esperaba '{esperado}' pero se encontró '{valor}' (token #{self.pos})"
            )
        self.pos += 1
        return valor

    # ---------- Expresiones ----------

    def factor(self):
        tipo, valor = self.token_actual()
        if tipo == "PUNTUACION" and valor == "(":
            self.log.append("factor → ( expr )")
            self.coincidir("PUNTUACION", "(")
            self.expr()
            self.coincidir("PUNTUACION", ")")
        elif tipo == "ID":
            self.log.append(f"factor → id ({valor})")
            self.coincidir("ID")
        elif tipo == "NUMERO_ENTERO":
            self.log.append(f"factor → numero_entero ({valor})")
            self.coincidir("NUMERO_ENTERO")
        elif tipo == "NUMERO_DECIMAL":
            self.log.append(f"factor → numero_decimal ({valor})")
            self.coincidir("NUMERO_DECIMAL")
        elif tipo == "CADENA":
            self.log.append(f"factor → cadena ({valor})")
            self.coincidir("CADENA")
        else:
            raise ErrorSintactico(
                f"Se esperaba un factor (id, número, cadena o '(') pero se encontró '{valor}' (token #{self.pos})"
            )

    def term(self):
        self.log.append("term → factor { (*|/|%) factor }")
        self.factor()
        while True:
            tipo, valor = self.token_actual()
            if tipo == "OP_ARITMETICO" and valor in ("*", "/", "%"):
                self.coincidir("OP_ARITMETICO", valor)
                self.factor()
            else:
                break

    def exprAr(self):
        self.log.append("exprAr → term { (+|-) term }")
        self.term()
        while True:
            tipo, valor = self.token_actual()
            if tipo == "OP_ARITMETICO" and valor in ("+", "-"):
                self.coincidir("OP_ARITMETICO", valor)
                self.term()
            else:
                break

    def exprRel(self):
        self.log.append("exprRel → exprAr [ OPREL exprAr ]")
        self.exprAr()
        tipo, valor = self.token_actual()
        if tipo == "OPREL":
            self.coincidir("OPREL", valor)
            self.exprAr()

    def exprAnd(self):
        self.log.append("exprAnd → exprRel { Y exprRel }")
        self.exprRel()
        while True:
            tipo, valor = self.token_actual()
            if tipo == "OP_LOGICO" and valor == "Y":
                self.coincidir("OP_LOGICO", "Y")
                self.exprRel()
            else:
                break

    def exprOr(self):
        self.log.append("exprOr → exprAnd { O exprAnd }")
        self.exprAnd()
        while True:
            tipo, valor = self.token_actual()
            if tipo == "OP_LOGICO" and valor == "O":
                self.coincidir("OP_LOGICO", "O")
                self.exprAnd()
            else:
                break

    def expr(self):
        self.log.append("expr → exprOr")
        self.exprOr()

    # ---------- Instrucciones ----------

    def bloque(self):
        self.log.append("bloque → { listaInstr }")
        self.coincidir("PUNTUACION", "{")
        self.listaInstr()
        self.coincidir("PUNTUACION", "}")

    def declaracion(self, tipo_valor):
        self.log.append(f"declaracion → {tipo_valor} id = expr ;")
        self.coincidir("PALABRA_CLAVE", tipo_valor)
        self.coincidir("ID")
        self.coincidir("PUNTUACION", "=")
        self.expr()
        self.coincidir("PUNTUACION", ";")

    def asignacion(self):
        self.log.append("asignacion → id = expr ;")
        self.coincidir("ID")
        self.coincidir("PUNTUACION", "=")
        self.expr()
        self.coincidir("PUNTUACION", ";")

    def si_instr(self):
        self.log.append("si → si ( expr ) bloque sinoOpt")
        self.coincidir("PALABRA_CLAVE", "si")
        self.coincidir("PUNTUACION", "(")
        self.expr()
        self.coincidir("PUNTUACION", ")")
        self.bloque()
        self.sinoOpt()

    def sinoOpt(self):
        tipo, valor = self.token_actual()
        if tipo == "PALABRA_CLAVE" and valor == "sino":
            self.log.append("sinoOpt → sino bloque")
            self.coincidir("PALABRA_CLAVE", "sino")
            self.bloque()
        else:
            self.log.append("sinoOpt → ε")

    def mientras_instr(self):
        self.log.append("mientras → mientras ( expr ) bloque")
        self.coincidir("PALABRA_CLAVE", "mientras")
        self.coincidir("PUNTUACION", "(")
        self.expr()
        self.coincidir("PUNTUACION", ")")
        self.bloque()

    def retorno_instr(self):
        self.log.append("retorno → retorno expr ;")
        self.coincidir("PALABRA_CLAVE", "retorno")
        self.expr()
        self.coincidir("PUNTUACION", ";")

    def instr(self):
        tipo, valor = self.token_actual()
        if tipo == "PALABRA_CLAVE" and valor in ("entero", "decimal", "texto"):
            self.declaracion(valor)
        elif tipo == "ID":
            self.asignacion()
        elif tipo == "PALABRA_CLAVE" and valor == "si":
            self.si_instr()
        elif tipo == "PALABRA_CLAVE" and valor == "mientras":
            self.mientras_instr()
        elif tipo == "PALABRA_CLAVE" and valor == "retorno":
            self.retorno_instr()
        else:
            raise ErrorSintactico(
                f"Se esperaba el inicio de una instrucción pero se encontró '{valor}' (token #{self.pos})"
            )

    def listaInstr(self):
        tipo, valor = self.token_actual()
        inicios = {"entero", "decimal", "texto", "si", "mientras", "retorno"}
        if tipo == "ID" or (tipo == "PALABRA_CLAVE" and valor in inicios):
            self.log.append("listaInstr → instr listaInstr")
            self.instr()
            self.listaInstr()
        else:
            self.log.append("listaInstr → ε")

    def programa(self):
        self.log.append("programa → listaInstr")
        self.listaInstr()
        tipo, valor = self.token_actual()
        if tipo != "$":
            raise ErrorSintactico(
                f"Sobra código después de un programa válido, empezando en '{valor}' (token #{self.pos})"
            )


def analizar_sintaxis(tokens):
    parser = Parser(tokens)
    try:
        parser.programa()
        return True, parser.log, None
    except ErrorSintactico as e:
        return False, parser.log, str(e)