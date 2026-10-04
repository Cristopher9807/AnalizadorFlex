# Analizador Léxico - Flex + Python (GUI)

Proyecto de la materia de Compiladores. Implementa un analizador
léxico usando **Flex**, con una interfaz gráfica en **Python/Tkinter** que
permite crear, editar, eliminar y analizar archivos de texto, sin usar la
consola.

## Requisitos

- Python 3.x instalado (incluye Tkinter por defecto en Windows).
- (Opcional, solo si se desea recompilar el analizador) Flex y GCC —
  por ejemplo mediante MSYS2/MinGW (`win_flex`, `gcc`).

## Cómo ejecutar

1. Descargar o clonar este repositorio.
2. Hacer doble clic en `iniciar.bat`.

Esto abre la interfaz gráfica. Desde ahí se puede:
- Ver la lista de archivos `.txt` de la carpeta.
- Crear un archivo nuevo (**Nuevo**).
- Editar el contenido de un archivo seleccionado.
- Guardar los cambios (**Guardar**).
- Eliminar un archivo (**Eliminar**).
- Analizar el archivo abierto (**Analizar**), mostrando los tokens
  generados en una tabla (tipo de token y valor).

## Lenguaje reconocido por el analizador

El analizador léxico reconoce los siguientes elementos:

| Categoría | Expresión regular / regla | Ejemplos | Token generado |
| --- | --- | --- | --- |
| Palabras clave | literales: `si`, `sino`, `mientras`, `entero`, `decimal`, `texto`, `retorno` | `si`, `entero` | `PALABRA_CLAVE` |
| Identificadores | `{LETRA}({LETRA}\|{DIGITO})*` | `x`, `contador`, `nombre_1` | `ID` |
| Números enteros | `{DIGITO}+` | `5`, `100` | `NUMERO_ENTERO` |
| Números decimales | `{DIGITO}+\.{DIGITO}+` | `3.14`, `0.5` | `NUMERO_DECIMAL` |
| Cadenas de texto | `\"[^\"]*\"` | `"hola mundo"` | `CADENA` |
| Comentarios | `\/\/[^\n]*` | `// esto es un comentario` | `COMENTARIO` |
| Operadores lógicos | literales: `Y`, `O` | `Y`, `O` | `OP_LOGICO` |
| Operadores relacionales | literales: `<=`, `<`, `>=`, `>`, `==`, `!=` | `<=`, `==` | `OPREL` |
| Operadores aritméticos | literales: `+ - * / %` | `+`, `%` | `OP_ARITMETICO` |
| Signos de puntuación | literales: `( ) { } ; =` | `(`, `;` | `PUNTUACION` |
| Espacios/tabs/saltos de línea | `[ \t\n]+` | — | (se ignoran, no generan token) |
| Símbolo no reconocido | `.` (cualquier otro carácter) | `@`, `#`, `&` | `ERROR_LEXICO` |

**Notas sobre precedencia de reglas** (importante para las pruebas):
- Las palabras clave se declaran **antes** que `{ID}` en el `.l`, porque
  Flex resuelve empates de longitud a favor de la regla que aparece primero.
  Sin ese orden, `entero` se reconocería como `ID` en lugar de `PALABRA_CLAVE`.
- Los operadores de dos caracteres (`<=`, `>=`, `==`, `!=`) se declaran
  **antes** que sus versiones de un solo carácter (`<`, `>`), porque Flex
  siempre prefiere la coincidencia más larga posible ("maximal munch").

### Ejemplo de código de prueba

entero x = 5;
decimal y = 3.14;
si (x <= 10 Y y > 1) {
retorno x + y;
} sino {
retorno 0;
}
// esto es un comentario
texto mensaje = "hola mundo";


## Cómo recompilar el analizador (opcional)

Si se modifica `analizador.l`, hay que regenerar el ejecutable:

win_flex analizador.l
gcc lex.yy.c -o analizador.exe


## Análisis sintáctico

Además del análisis léxico, el proyecto incluye un **analizador sintáctico**
implementado en Python (`parser.py`), integrado en la misma interfaz
gráfica. En la interfaz hay un desplegable **"Analizador"** con dos opciones:

- **Léxico**: comportamiento original, solo muestra la tabla de tokens.
- **Sintáctico**: además de los tokens, ejecuta el analizador sintáctico
  sobre esos mismos tokens y muestra, en un panel nuevo, la derivación
  paso a paso y el veredicto final (cadena aceptada o el error de sintaxis
  encontrado, indicando qué se esperaba y qué se encontró).

Si el archivo analizado tiene algún `ERROR_LEXICO`, el análisis sintáctico
no se ejecuta — primero hay que corregir el error léxico.

### Gramática reconocida

El analizador sintáctico se implementó como un **analizador descendente
predictivo (descenso recursivo)**: una función por cada no terminal, que
decide qué producción aplicar mirando el token actual. La gramática es la
siguiente:

programa → listaInstr
listaInstr → instr listaInstr | ε
instr → declaracion | asignacion | si | mientras | retorno
tipo → entero | decimal | texto
declaracion → tipo id = expr ;
asignacion → id = expr ;
si → si ( expr ) bloque sinoOpt
sinoOpt → sino bloque | ε
mientras → mientras ( expr ) bloque
retorno → retorno expr ;
bloque → { listaInstr }

expr → exprOr
exprOr → exprAnd { O exprAnd }
exprAnd → exprRel { Y exprRel }
exprRel → exprAr [ OPREL exprAr ]
exprAr → term { (+|-) term }
term → factor { (*|/|%) factor }
factor → ( expr ) | id | numero_entero | numero_decimal | cadena


Esta gramática no tiene recursividad por la izquierda y cada alternativa se
puede elegir viendo un solo token de anticipación, por lo que es apta para
análisis descendente predictivo sin necesidad de retroceso (*backtracking*).


### Casos de prueba (sintáctico)

| Entrada | Resultado esperado | Resultado obtenido |
| --- | --- | --- |
| Programa completo con declaraciones, `si/sino`, `retorno`, comentario y cadena | Aceptada | ✔️ Aceptada |
| `entero x = 52` (sin `;`) | Error de sintaxis, falta `;` | ✔️ `Se esperaba ';' pero se encontró '$'` |
| `si x <= 10 { retorno x; }` (sin `(` después de `si`) | Error de sintaxis, falta `(` | ✔️ `Se esperaba '(' pero se encontró 'x'` |

## Estructura del proyecto

- `analizador.l` — código fuente del analizador léxico, escrito en Flex.
- `lex.yy.c` — código C generado automáticamente por Flex a partir de `analizador.l`.
- `analizador.exe` — ejecutable ya compilado del analizador léxico.
- `interfaz.py` — interfaz gráfica en Python/Tkinter que gestiona los archivos y ejecuta el analizador.
- `iniciar.bat` — lanzador que abre la interfaz gráfica sin mostrar consola.

## Archivos agregados para el análisis sintáctico

- `parser.py` — analizador sintáctico (descenso recursivo) en Python.
  Recibe la lista de tokens que produce `analizador.exe` y determina si
  forman un programa válido según la gramática de la sección
  "Análisis sintáctico", generando además el log de derivación paso a paso.
- `interfaz.py` se amplió con un selector **"Analizador: Léxico / Sintáctico"**
  y un panel nuevo que muestra el resultado del análisis sintáctico cuando
  ese modo está seleccionado.

## Autor

Cristopher Grullón Pérez 1-17-0292.