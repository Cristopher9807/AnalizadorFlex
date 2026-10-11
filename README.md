# Analizador Léxico, Sintáctico y Semántico - Flex + Python (GUI)

Proyecto de la materia de Compiladores. Implementa un analizador
léxico usando **Flex**, un analizador sintáctico (descenso recursivo) y un
analizador semántico (tabla de símbolos y verificación de tipos) en
**Python**, con una interfaz gráfica en **Python/Tkinter** que permite
crear, abrir, editar, eliminar y analizar archivos de texto, sin usar la consola.

## Requisitos

- Para usar el ejecutable final (`EJECUTABLE/AnalizadorCompiladores.exe`):
  ninguno, no requiere tener Python instalado.
- Para correr o modificar el código fuente: Python 3.x instalado (incluye
  Tkinter por defecto en Windows).
- (Opcional, solo si se desea recompilar el analizador léxico) Flex y GCC —
  por ejemplo mediante MSYS2/MinGW (`win_flex`, `gcc`).
- (Opcional, solo si se desea regenerar el ejecutable) PyInstaller
  (`pip install pyinstaller`).

## Cómo ejecutar

**Opción recomendada (no requiere tener Python instalado):**

1. Entra a la carpeta `EJECUTABLE/`.
2. Haz doble clic en `AnalizadorCompiladores.exe`.

**Para correr o modificar el código fuente directamente:**

1. Asegúrate de tener Python 3.x instalado.
2. Abre una terminal en la carpeta del proyecto y corre:

```
python interfaz.py
```

Al correr desde el código fuente, la interfaz lee y guarda los archivos
`.txt` en la carpeta `EJECUTABLE/`, igual que lo hace el ejecutable, de modo
que se ven los mismos archivos en ambos casos.

En cualquiera de los dos casos, la interfaz permite:
- Ver la lista de archivos `.txt` de la carpeta.
- Crear un archivo nuevo (**Nuevo**).
- Abrir un archivo `.txt` de cualquier ubicación (**Abrir...**): se copia a
  la carpeta de trabajo y queda en la lista.
- Editar el contenido de un archivo seleccionado.
- Guardar los cambios (**Guardar**).
- Eliminar un archivo (**Eliminar**).
- Elegir, en el desplegable **Analizador**, entre **Léxico**, **Sintáctico**
  o **Semántico**. Al cambiar de analizador, el archivo abierto se guarda y
  se mantiene en el editor.
- Analizar el archivo abierto (**Analizar**), mostrando los tokens
  generados y, según el modo: la derivación paso a paso y el veredicto
  (Sintáctico), o la tabla de símbolos, las comprobaciones y los errores
  semánticos (Semántico).

**Filtrado de archivos por analizador:** en modo **Semántico** la lista
muestra los archivos cuyo nombre empieza por `Semantico`; en modo Léxico y
Sintáctico muestra el resto. Los archivos abiertos con **Abrir...** o creados
en la sesión se muestran siempre. Si se crea un archivo nuevo en modo
Semántico, el programa le agrega el prefijo `Semantico` automáticamente.

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

```
entero x = 5;
decimal y = 3.14;
si (x <= 10 Y y > 1) {
retorno x + y;
} sino {
retorno 0;
}
// esto es un comentario
texto mensaje = "hola mundo";
```

## Cómo recompilar el analizador léxico (opcional)

Si se modifica `analizador.l`, hay que regenerar el ejecutable:

```
win_flex analizador.l
gcc lex.yy.c -o analizador.exe
```

## Análisis sintáctico

Además del análisis léxico, el proyecto incluye un **analizador sintáctico**
implementado en Python (`parser.py`), integrado en la misma interfaz
gráfica. En la interfaz hay un desplegable **"Analizador"** con tres opciones:

- **Léxico**: comportamiento original, solo muestra la tabla de tokens.
- **Sintáctico**: además de los tokens, ejecuta el analizador sintáctico
  sobre esos mismos tokens y muestra, en un panel nuevo, la derivación
  paso a paso y el veredicto final (cadena aceptada o el error de sintaxis
  encontrado, indicando qué se esperaba y qué se encontró).
- **Semántico**: ver la sección "Análisis semántico".

Si el archivo analizado tiene algún `ERROR_LEXICO`, el análisis sintáctico
no se ejecuta — primero hay que corregir el error léxico.

### Gramática reconocida

El analizador sintáctico se implementó como un **analizador descendente
predictivo (descenso recursivo)**: una función por cada no terminal, que
decide qué producción aplicar mirando el token actual. La gramática es la
siguiente:

```
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
```

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

## Análisis semántico

El **analizador semántico** está implementado en Python (`semantico.py`) e
integrado en la misma interfaz (modo **Semántico**). Revisa que un programa
que ya es sintácticamente correcto además tenga sentido: que las variables
existan, que los tipos sean compatibles y que las condiciones sean válidas.

Para que se ejecute, el archivo no debe tener errores léxicos ni de sintaxis;
si los tiene, la interfaz los informa y no hace el análisis semántico.

### Cómo funciona

- **Tabla de símbolos:** una pila de ámbitos. Cada `{ }` abre un ámbito nuevo
  y al cerrarlo se descartan las variables declaradas dentro. Cada declaración
  se guarda con su nombre, tipo y nivel de ámbito.
- **Atributos:** el tipo de cada expresión se calcula de abajo hacia arriba
  (atributo sintetizado, devuelto por cada función de expresión) y el ámbito
  se pasa de arriba hacia abajo (atributo heredado, la pila de ámbitos).
- **Errores:** se acumulan todos, sin detenerse en el primero. Cuando una
  expresión tiene error, su tipo pasa a `error` para no provocar errores en
  cascada.

### Reglas verificadas

| Regla | Ejemplo con error |
| --- | --- |
| No se puede declarar dos veces una variable en el mismo ámbito | `entero x = 5; entero x = 6;` |
| Toda variable debe estar declarada antes de usarse | `entero r = y + 1;` |
| El valor asignado debe ser compatible con el tipo de la variable | `texto t = 10;` |
| `entero` cabe en `decimal`, pero no al revés | `entero x = 1.5;` |
| `entero` operado con `decimal` da `decimal` | `x + y` con `y` decimal |
| `texto + texto` es concatenación | `"a" + "b"` |
| Las comparaciones dan `booleano` y comparan número con número o texto con texto | `1 < "a"` |
| `Y` y `O` solo aceptan `booleano` | `x Y 1` |
| La condición de `si` y `mientras` debe ser `booleano` | `mientras (x)` |
| Una variable no existe fuera del bloque donde se declaró | usar `a` fuera de su `{ }` |

### Salida en la interfaz

En modo **Semántico** el panel de resultados muestra:

1. La **tabla de símbolos** (nombre, tipo y ámbito de cada variable).
2. Las **comprobaciones realizadas**.
3. El **resultado**: `ANÁLISIS SEMÁNTICO CORRECTO` o la lista de errores
   semánticos encontrados.

### Casos de prueba (semántico)

Archivos incluidos en `EJECUTABLE/`:

| Archivo | Resultado esperado |
| --- | --- |
| `Semantico correcto.txt` | ✔️ Análisis semántico correcto |
| `Semantico errores.txt` | ✔️ 6 errores semánticos |

Contenido de `Semantico correcto.txt`:

```
entero x = 5;
decimal y = 2.5;
texto nombre = "Criss";
decimal z = x + y;
si (z > 3) {
    entero w = x * 2;
    x = w;
}
```

Contenido de `Semantico errores.txt` (variable repetida, tipo incompatible,
variable no declarada, condición no booleana, decimal asignado a entero y
variable usada fuera de su ámbito):

```
entero x = 5;
entero x = 6;
texto t = 10;
entero r = y + 1;
mientras (x) {
    x = 1.5;
}
si (1 < 2) {
    entero a = 1;
}
a = 2;
```

## Ejecutable

Además del código fuente, el proyecto incluye un ejecutable autosuficiente
(no requiere tener Python instalado) generado con **PyInstaller**:

- `EJECUTABLE/AnalizadorCompiladores.exe` — ejecutable final. Incluye
  empaquetado adentro el analizador léxico (`analizador.exe`). Al abrirlo,
  gestiona los archivos `.txt` que estén en esa misma carpeta (por eso
  `Prueba.txt`, `Prueba 2.txt` y los archivos `Semantico *.txt` están ahí
  también, como ejemplos listos para probar).

### Cómo regenerar el ejecutable (opcional)

El ejecutable es una copia del código del momento en que se generó: si se
modifica algún `.py`, hay que volver a generarlo. Para eso basta con hacer
doble clic en `generar_exe.bat`, que cierra el programa si está abierto y
genera el ejecutable directamente en `EJECUTABLE/`.

Equivale a ejecutar (requiere `pip install pyinstaller`):

```
python -m PyInstaller --noconfirm --onefile --windowed --add-data "analizador.exe;." --name AnalizadorCompiladores --distpath EJECUTABLE interfaz.py
```

La configuración de este empaquetado queda guardada en
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
- `semantico.py` — analizador semántico en Python. Recibe los mismos tokens
  y, con una tabla de símbolos por ámbitos, verifica declaraciones, usos de
  variables y compatibilidad de tipos, devolviendo la tabla de símbolos, el
  log de comprobaciones y la lista de errores.
- `interfaz.py` — interfaz gráfica en Python/Tkinter que gestiona los
  archivos, ejecuta el analizador léxico y, según el modo elegido
  ("Sintáctico" o "Semántico"), también el sintáctico y el semántico.
- `generar_exe.bat` — script que regenera el ejecutable en `EJECUTABLE/`
  con un doble clic.
- `AnalizadorCompiladores.spec` — configuración de empaquetado generada por
  PyInstaller, usada para regenerar el ejecutable.
- `EJECUTABLE/` — carpeta con el ejecutable final
  (`AnalizadorCompiladores.exe`) y los archivos `.txt` de ejemplo.

## Autor

Cristopher Grullón Pérez 1-17-0292.