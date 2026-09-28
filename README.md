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


## Estructura del proyecto

- `analizador.l` — código fuente del analizador léxico, escrito en Flex.
- `lex.yy.c` — código C generado automáticamente por Flex a partir de `analizador.l`.
- `analizador.exe` — ejecutable ya compilado del analizador léxico.
- `interfaz.py` — interfaz gráfica en Python/Tkinter que gestiona los archivos y ejecuta el analizador.
- `iniciar.bat` — lanzador que abre la interfaz gráfica sin mostrar consola.

## Autor

Cristopher Grullón Pérez 1-17-0292.