# Analizador Léxico y Sintáctico - Flex + Python (GUI)

Proyecto de la materia de Compiladores. Implementa un analizador
léxico usando **Flex**, y un analizador sintáctico (descenso recursivo)
en **Python**, con una interfaz gráfica en **Python/Tkinter** que permite
crear, editar, eliminar y analizar archivos de texto, sin usar la consola.

## Requisitos

- Para usar el ejecutable final (`EJECUTABLE/AnalizadorCompiladores.exe`):
  ninguno, no requiere tener Python instalado.
- Para correr o modificar el código fuente: Python 3.x instalado (incluye
  Tkinter por defecto en Windows).
- (Opcional, solo si se desea recompilar el analizador léxico) Flex y GCC —
  por ejemplo mediante MSYS2/MinGW (`win_flex`, `gcc`).

## Cómo ejecutar

**Opción recomendada (no requiere tener Python instalado):**

1. Entra a la carpeta `EJECUTABLE/`.
2. Haz doble clic en `AnalizadorCompiladores.exe`.

**Para correr o modificar el código fuente directamente:**

1. Asegúrate de tener Python 3.x instalado.
2. Abre una terminal en la carpeta del proyecto y corre:

python interfaz.py


En cualquiera de los dos casos, la interfaz permite:
- Ver la lista de archivos `.txt` de la carpeta.
- Crear un archivo nuevo (**Nuevo**).
- Editar el contenido de un archivo seleccionado.
- Guardar los cambios (**Guardar**).
- Eliminar un archivo (**Eliminar**).
- Elegir, en el desplegable **Analizador**, entre **Léxico** o **Sintáctico**.
- Analizar el archivo abierto (**Analizar**), mostrando los tokens
  generados y, en modo Sintáctico, la derivación paso a paso y el veredicto.

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


## Cómo recompilar el analizador léxico (opcional)

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

**Nota sobre el "else colgante":** el cuerpo de `si`/`sino` siempre exige un
`bloque` con llaves (`{ listaInstr }`), nunca una instrucción suelta. Esto
elimina por diseño la ambigüedad clásica del "dangling else" (a qué `si` se
asocia un `sino` cuando hay varios `si` anidados sin llaves): en este
lenguaje no existe forma de escribir esa construcción ambigua.

### Casos de prueba (sintáctico)

| Entrada | Resultado esperado | Resultado obtenido |
| --- | --- | --- |
| Programa completo con declaraciones, `si/sino`, `retorno`, comentario y cadena | Aceptada | ✔️ Aceptada |
| `entero x = 52` (sin `;`) | Error de sintaxis, falta `;` | ✔️ `Se esperaba ';' pero se encontró '$'` |
| `si x <= 10 { retorno x; }` (sin `(` después de `si`) | Error de sintaxis, falta `(` | ✔️ `Se esperaba '(' pero se encontró 'x'` |

## Ejecutable

Además del código fuente, el proyecto incluye un ejecutable autosuficiente
(no requiere tener Python instalado) generado con **PyInstaller**:

- `EJECUTABLE/AnalizadorCompiladores.exe` — ejecutable final. Incluye
  empaquetado adentro el analizador léxico (`analizador.exe`). Al abrirlo,
  gestiona los archivos `.txt` que estén en esa misma carpeta (por eso
  `Prueba.txt` y `Prueba 2.txt` están ahí también, como ejemplos listos
  para probar).

### Cómo regenerar el ejecutable (opcional)

Si se modifica el código fuente, el ejecutable se vuelve a generar con:

pip install pyinstaller
pyinstaller --onefile --windowed --add-data "analizador.exe;." --name AnalizadorCompiladores interfaz.py


El resultado queda en `dist/AnalizadorCompiladores.exe` (luego se puede
mover/renombrar la carpeta `dist` a `EJECUTABLE` si se desea). La
configuración de este empaquetado queda guardada en
`AnalizadorCompiladores.spec`.

## Estructura del proyecto

- `analizador.l` — código fuente del analizador léxico, escrito en Flex.
- `lex.yy.c` — código C generado automáticamente por Flex a partir de `analizador.l`.
- `analizador.exe` — ejecutable compilado del analizador léxico puro (sin
  interfaz). Es un componente interno que usa `interfaz.py` por detrás,
  necesario solo para correr el proyecto desde el código fuente.

  > **Nota:** `analizador.exe` no está pensado para abrirse directamente
  > con doble clic (es un programa de consola que espera recibir un
  > archivo como argumento). Para eso está
  > `EJECUTABLE/AnalizadorCompiladores.exe`.
- `parser.py` — analizador sintáctico (descenso recursivo) en Python.
  Recibe la lista de tokens que produce `analizador.exe` y determina si
  forman un programa válido según la gramática de la sección
  "Análisis sintáctico", generando además el log de derivación paso a paso.
- `interfaz.py` — interfaz gráfica en Python/Tkinter que gestiona los
  archivos, ejecuta el analizador léxico y, si se elige el modo
  "Sintáctico", también el analizador sintáctico.
- `AnalizadorCompiladores.spec` — configuración de empaquetado generada por
  PyInstaller, usada para regenerar el ejecutable.
- `EJECUTABLE/` — carpeta con el ejecutable final
  (`AnalizadorCompiladores.exe`) y los archivos `.txt` de ejemplo.

## Autor

Cristopher Grullón Pérez 1-17-0292.