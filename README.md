# Documentación del lenguaje y del traductor de código

**Autor:** Cristopher Grullón Pérez (1-17-0292)
**Materia:** Compiladores, UTESA
**Capítulo:** 6 – Generación de código intermedio

---

## 1. Descripción general

El proyecto es un compilador pequeño, construido por etapas (una por capítulo), con una interfaz gráfica en Tkinter. La última etapa es un **traductor de código**: toma un programa escrito en nuestro lenguaje (palabras clave en español) y lo traduce a otro lenguaje.

| Destino | Extensión | Qué es |
| --- | --- | --- |
| Python | `.py` | Lenguaje interpretado de alto nivel |
| JavaScript | `.js` | Lenguaje de la web (se ejecuta con Node.js) |
| C++ | `.cpp` | Lenguaje compilado, con tipos estáticos |
| Código de tres direcciones | `.tac` | Representación intermedia del capítulo 6 |

### 1.1 Flujo completo

```
 programa fuente (.txt)
        |
        v
 [ analizador.exe (Flex) ]      Etapa léxica      -> tokens "TIPO<TAB>valor"
        |
        v
 [ parser.py ]                  Etapa sintáctica  -> acepta o rechaza (derivación)
        |
        v
 [ semantico.py ]               Etapa semántica   -> tabla de símbolos y tipos
        |
        v
 [ traductor.py ]               Traductor         -> AST + comprobación de tipos
        |                                            + generador de código
        v
 Python / JavaScript / C++ / código de tres direcciones
```

El traductor sigue la estructura clásica de un compilador:

- **Front-end** (analiza el programa): `leer_tokens` y `construir_ast`. Produce un **árbol sintáctico abstracto (AST)** con el tipo de cada expresión.
- **Back-end** (genera código): una función por lenguaje destino (`_generar_python`, `_generar_js`, `_generar_cpp`, `_generar_tac`).

Gracias a esta separación, agregar un lenguaje nuevo solo requiere escribir un generador nuevo; el front-end no cambia (idea de la sección 6.1 del libro: *m* lenguajes y *n* máquinas necesitan *m + n* piezas, no *m × n* compiladores).

---

## 2. El lenguaje fuente

### 2.1 Elementos léxicos (tokens)

| Token | Descripción | Ejemplos |
| --- | --- | --- |
| `PALABRA_CLAVE` | Palabras reservadas | `si`, `sino`, `mientras`, `entero`, `decimal`, `texto`, `retorno` |
| `ID` | Identificador: letra o `_`, seguido de letras, dígitos o `_` | `suma`, `_x`, `total2` |
| `NUMERO_ENTERO` | Uno o más dígitos | `0`, `42` |
| `NUMERO_DECIMAL` | Dígitos, punto y dígitos | `3.14`, `13.0` |
| `CADENA` | Texto entre comillas dobles (sin comillas dentro) | `"hola"` |
| `COMENTARIO` | Desde `//` hasta el fin de la línea | `// esto es un comentario` |
| `OP_LOGICO` | Operadores lógicos `Y` (y) y `O` (o) | `Y`, `O` |
| `OPREL` | Operadores relacionales | `<`, `<=`, `>`, `>=`, `==`, `!=` |
| `OP_ARITMETICO` | Operadores aritméticos | `+`, `-`, `*`, `/`, `%` |
| `PUNTUACION` | Símbolos de puntuación | `(` `)` `{` `}` `;` `=` |
| `ERROR_LEXICO` | Cualquier símbolo no reconocido | `@` |

Los espacios, tabuladores y saltos de línea se ignoran.

### 2.2 Gramática

```
programa      -> listaInstr
listaInstr    -> instr listaInstr | ε
instr         -> declaracion | asignacion | si | mientras | retorno | COMENTARIO

declaracion   -> tipo ID '=' expr ';'
tipo          -> 'entero' | 'decimal' | 'texto'
asignacion    -> ID '=' expr ';'
si            -> 'si' '(' expr ')' bloque [ 'sino' bloque ]
mientras      -> 'mientras' '(' expr ')' bloque
retorno       -> 'retorno' expr ';'
bloque        -> '{' listaInstr '}'

expr          -> exprY { 'O' exprY }
exprY         -> exprRel { 'Y' exprRel }
exprRel       -> exprAr [ OPREL exprAr ]
exprAr        -> termino { ('+' | '-') termino }
termino       -> factor { ('*' | '/' | '%') factor }
factor        -> '(' expr ')' | ID | NUMERO_ENTERO | NUMERO_DECIMAL | CADENA
```

La gramática no tiene recursividad por la izquierda (las repeticiones se escriben con `{ ... }`), por eso se puede analizar con **descenso recursivo**.

**Nota sobre el `else` colgante:** `si` y `sino` siempre llevan bloque con llaves `{ }`. No existe la forma `si (x) instruccion;`, así que la ambigüedad del *dangling else* (capítulo 4) no puede aparecer en este lenguaje.

### 2.3 Precedencia y asociatividad

De menor a mayor precedencia (todos asocian por la izquierda):

| Nivel | Operadores |
| --- | --- |
| 1 (menor) | `O` |
| 2 | `Y` |
| 3 | `<` `<=` `>` `>=` `==` `!=` (no se encadenan: `a < b < c` no es válido) |
| 4 | `+` `-` |
| 5 (mayor) | `*` `/` `%` |

### 2.4 Tipos y reglas de tipos

El lenguaje tiene tres tipos: `entero`, `decimal` y `texto`. Las comparaciones y los operadores `Y`/`O` producen un valor lógico que solo se usa como condición.

| Regla | Detalle |
| --- | --- |
| Declaración | Toda variable se declara con tipo e inicialización: `entero x = 5;` |
| Uso | Una variable debe declararse antes de usarse |
| Ámbitos | Cada bloque `{ }` abre un ámbito nuevo. No se puede declarar el mismo nombre dos veces en el mismo ámbito; un bloque interno puede ocultar un nombre externo |
| Asignación | `entero ← entero`, `decimal ← decimal`, `decimal ← entero` (ampliación automática), `texto ← texto`. Cualquier otra combinación es un error |
| Aritmética | `+ - * /` solo con `entero` y `decimal`. Si algún operando es `decimal`, el resultado es `decimal`; si ambos son `entero`, el resultado es `entero` |
| Módulo `%` | Solo con operandos `entero` |
| Concatenación | `texto + texto` produce `texto` |
| Comparación | Se comparan dos números entre sí o dos textos entre sí |
| Lógicos | `Y` y `O` no aceptan `texto` |
| Condición | La condición de `si` y `mientras` no puede ser `texto` |
| División | `entero / entero` es **división entera** (como en C) |
| `retorno` | Devuelve un valor al terminar el programa |

### 2.5 Ejemplo de programa

```
// Programa de prueba para el traductor
entero i = 1;
entero suma = 0;
mientras (i <= 10) {
    suma = suma + i;
    i = i + 1;
}
decimal promedio = suma / 4;
texto saludo = "hola" + " mundo";
si (suma > 50 Y promedio >= 13.0) {
    entero descuento = 5;
    suma = suma - descuento;
} sino {
    suma = 0;
}
retorno suma;
```

---

## 3. El traductor

### 3.1 Etapas

1. **Lectura de tokens** (`leer_tokens`): convierte la salida de `analizador.exe` (líneas `TIPO<TAB>valor`) en una lista de pares.
2. **Análisis sintáctico y de tipos** (`construir_ast`): parser de descenso recursivo que construye el AST. Mantiene una pila de tablas de símbolos (una por bloque) y calcula el tipo de cada expresión **mientras analiza** (atributos sintetizados, capítulo 5).
3. **Generación de código** (`generar`): recorre el AST y escribe el programa en el lenguaje destino.

### 3.2 Nodos del AST

| Nodo | Representa |
| --- | --- |
| `Programa` | Lista de instrucciones |
| `Declaracion`, `Asignacion` | `tipo id = expr;` y `id = expr;` |
| `Si`, `Mientras` | Condición + bloque (y bloque `sino` opcional) |
| `Retorno` | `retorno expr;` |
| `Comentario` | Los comentarios se conservan y se traducen |
| `Binaria` | Operación con operador, dos hijos y tipo |
| `Numero`, `Cadena`, `Variable` | Hojas del árbol |

### 3.3 Tabla de equivalencias

| Construcción fuente | Python | JavaScript | C++ |
| --- | --- | --- | --- |
| Programa | `def main():` + llamada | `function main()` + llamada | `int main()` |
| `entero x = 5;` | `x = 5` | `let x = 5;` | `int x = 5;` |
| `decimal y = 2.5;` | `y = 2.5` | `let y = 2.5;` | `double y = 2.5;` |
| `texto t = "a";` | `t = "a"` | `let t = "a";` | `std::string t = "a";` |
| `si (c) { } sino { }` | `if c:` / `else:` | `if (c) { } else { }` | `if (c) { } else { }` |
| `mientras (c) { }` | `while c:` | `while (c) { }` | `while (c) { }` |
| `retorno e;` | `return e` | `return e;` | `return e;` |
| `Y` / `O` | `and` / `or` | `&&` / `\|\|` | `&&` / `\|\|` |
| `==` / `!=` | `==` / `!=` | `===` / `!==` | `==` / `!=` |
| `entero / entero` | `int(a / b)` | `Math.trunc(a / b)` | `a / b` |
| Concatenar textos | `a + b` | `a + b` | `std::string(a) + std::string(b)` |
| Comentario `// x` | `# x` | `// x` | `// x` |

### 3.4 Decisiones de diseño

- **Paréntesis mínimos.** El AST no guarda los paréntesis del original. Al generar, se vuelven a poner solo donde la precedencia lo exige (por ejemplo `10 - (3 - 2)`, pero `10 - 3 - 2`).
- **Nombres reservados.** Si un identificador coincide con una palabra reservada del destino (`class`, `int`, `main`, ...), se le agrega un guion bajo (`class_`).
- **Bloques vacíos en Python.** Python no admite bloques sin instrucciones, así que se agrega `pass`.
- **Ampliación de tipos.** En Python, un entero asignado a un `decimal` se convierte con `float(...)`.
- **`retorno` en C++.** `main` devuelve `int`: un `retorno` decimal se convierte con `(int)` y un `retorno` de texto se rechaza con un mensaje claro. Si el programa no termina en `retorno`, se agrega `return 0;`.

### 3.5 Código de tres direcciones (representación intermedia)

El cuarto destino no es un lenguaje de programación, sino el **código intermedio** del capítulo 6. Cada instrucción tiene como máximo un operador:

| Forma | Ejemplo |
| --- | --- |
| Operación binaria | `t1 = suma / 4` |
| Copia | `x = t1` |
| Salto incondicional | `goto L1` |
| Salto si es falso | `ifFalse i <= 10 goto L2` |
| Etiqueta | `L1:` |
| Retorno | `return suma` |
| Conversión de tipo | `promedio = (float) t1` |

- Los temporales son `t1, t2, ...` y las etiquetas `L1, L2, ...`.
- `si` genera un `ifFalse` que salta al final (o al `sino`).
- `mientras` genera una etiqueta de inicio, un `ifFalse` de salida y un `goto` de regreso (esquema de la figura 6.35).
- Las conversiones `entero → decimal` se hacen explícitas con `(float)` (sección 6.5.2).
- `x = a op b` se genera directamente, sin temporal ni copia intermedia.
- Los operadores `Y` / `O` se calculan como valores (`t = a && b`), sin evaluación por cortocircuito.

### 3.6 Ejemplo completo

Programa fuente: el de la sección 2.5.

**Python**

```python
# Código generado por el traductor (destino: Python)

def main():
    # Programa de prueba para el traductor
    i = 1
    suma = 0
    while i <= 10:
        suma = suma + i
        i = i + 1
    promedio = float(int(suma / 4))
    saludo = "hola" + " mundo"
    if suma > 50 and promedio >= 13.0:
        descuento = 5
        suma = suma - descuento
    else:
        suma = 0
    return suma

if __name__ == "__main__":
    main()
```

**JavaScript**

```javascript
// Código generado por el traductor (destino: JavaScript)

function main() {
    // Programa de prueba para el traductor
    let i = 1;
    let suma = 0;
    while (i <= 10) {
        suma = suma + i;
        i = i + 1;
    }
    let promedio = Math.trunc(suma / 4);
    let saludo = "hola" + " mundo";
    if (suma > 50 && promedio >= 13.0) {
        let descuento = 5;
        suma = suma - descuento;
    } else {
        suma = 0;
    }
    return suma;
}

main();
```

**C++**

```cpp
// Código generado por el traductor (destino: C++)
#include <iostream>
#include <string>

int main() {
    // Programa de prueba para el traductor
    int i = 1;
    int suma = 0;
    while (i <= 10) {
        suma = suma + i;
        i = i + 1;
    }
    double promedio = suma / 4;
    std::string saludo = std::string("hola") + std::string(" mundo");
    if (suma > 50 && promedio >= 13.0) {
        int descuento = 5;
        suma = suma - descuento;
    } else {
        suma = 0;
    }
    return suma;
}
```

**Código de tres direcciones**

```
// Código intermedio de tres direcciones (capítulo 6)
    // Programa de prueba para el traductor
    i = 1
    suma = 0
L1:
    ifFalse i <= 10 goto L2
    suma = suma + i
    i = i + 1
    goto L1
L2:
    t1 = suma / 4
    promedio = (float) t1
    saludo = "hola" + " mundo"
    t2 = suma > 50
    t3 = promedio >= 13.0
    t4 = t2 && t3
    ifFalse t4 goto L3
    descuento = 5
    suma = suma - descuento
    goto L4
L3:
    suma = 0
L4:
    return suma
```

Al ejecutar los tres programas (Python, JavaScript y C++) el resultado es el mismo: **50**.

### 3.7 Errores que detecta

| Tipo | Ejemplo | Mensaje |
| --- | --- | --- |
| Léxico | `entero z = 5 @ 3;` | `Error léxico: simbolo no reconocido: @` |
| Sintaxis | `entero a = 1` (falta `;`) | `Error de sintaxis: se esperaba ';' ...` |
| Sintaxis | bloque sin cerrar | `falta cerrar un bloque con '}'` |
| Variable no declarada | `entero b = a + c;` sin declarar `c` | `la variable 'c' no ha sido declarada` |
| Redeclaración | `entero a = 1; entero a = 2;` | `ya fue declarada en este ámbito` |
| Tipos | `entero a = "hola";` | `no se puede asignar texto a 'a' (que es entero)` |
| Tipos | `decimal a = 5.0 % 2;` | `el operador '%' solo acepta enteros` |

### 3.8 Limitaciones conocidas

- El lenguaje no tiene instrucción de impresión ni funciones definidas por el usuario, así que el único resultado observable de un programa es el valor de `retorno`.
- En C++, el valor de `retorno` se usa como código de salida del programa (el sistema operativo lo limita a 0–255).
- Los mensajes de error no indican número de línea, porque los tokens de `analizador.exe` no incluyen esa información.
- La división entera y el módulo con operandos negativos pueden diferir entre lenguajes (el lenguaje fuente no tiene números negativos literales).

---

## 4. Estructura del proyecto

| Archivo | Función |
| --- | --- |
| `analizador.l` | Código fuente Flex (análisis léxico) |
| `lex.yy.c`, `analizador.exe` | Generados por Flex y gcc |
| `parser.py` | Analizador sintáctico (descenso recursivo) |
| `semantico.py` | Analizador semántico (tabla de símbolos y tipos) |
| `traductor.py` | **Traductor de código** (AST + generadores) |
| `interfaz.py` | Interfaz gráfica (Tkinter) |
| `generar_exe.bat` | Genera `EJECUTABLE\AnalizadorCompiladores.exe` con PyInstaller |
| `DOCUMENTACION.md` | Este documento |
| `EJECUTABLE/` | Ejecutable final y archivos `.txt` de prueba |

### Cómo usar el traductor

1. Abrir `AnalizadorCompiladores.exe` (o ejecutar `python interfaz.py`).
2. Elegir **Traductor** en el desplegable *Analizador*.
3. Elegir el lenguaje destino.
4. Abrir o escribir un programa y pulsar **Analizar**.
5. Se muestran los tokens, el árbol sintáctico y el código traducido. El botón de guardar escribe el resultado con la extensión del lenguaje destino.
