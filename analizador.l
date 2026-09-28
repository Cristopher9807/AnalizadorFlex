%option noyywrap

LETRA   [a-zA-Z_]
DIGITO  [0-9]
ID      {LETRA}({LETRA}|{DIGITO})*
ENTERO   {DIGITO}+
DECIMAL  {DIGITO}+\.{DIGITO}+

%%

si          { printf("PALABRA_CLAVE\t%s\n", yytext); }
sino        { printf("PALABRA_CLAVE\t%s\n", yytext); }
mientras    { printf("PALABRA_CLAVE\t%s\n", yytext); }
entero      { printf("PALABRA_CLAVE\t%s\n", yytext); }
decimal     { printf("PALABRA_CLAVE\t%s\n", yytext); }
texto       { printf("PALABRA_CLAVE\t%s\n", yytext); }
retorno     { printf("PALABRA_CLAVE\t%s\n", yytext); }

"Y"         { printf("OP_LOGICO\t%s\n", yytext); }
"O"         { printf("OP_LOGICO\t%s\n", yytext); }

{ID}        { printf("ID\t%s\n", yytext); }
{DECIMAL}   { printf("NUMERO_DECIMAL\t%s\n", yytext); }
{ENTERO}    { printf("NUMERO_ENTERO\t%s\n", yytext); }

\"[^\"]*\"  { printf("CADENA\t%s\n", yytext); }
\/\/[^\n]*  { printf("COMENTARIO\t%s\n", yytext); }

"<="        { printf("OPREL\t%s\n", yytext); }
"<"         { printf("OPREL\t%s\n", yytext); }
">="        { printf("OPREL\t%s\n", yytext); }
">"         { printf("OPREL\t%s\n", yytext); }
"=="        { printf("OPREL\t%s\n", yytext); }
"!="        { printf("OPREL\t%s\n", yytext); }

"+"         { printf("OP_ARITMETICO\t%s\n", yytext); }
"-"         { printf("OP_ARITMETICO\t%s\n", yytext); }
"*"         { printf("OP_ARITMETICO\t%s\n", yytext); }
"/"         { printf("OP_ARITMETICO\t%s\n", yytext); }
"%"         { printf("OP_ARITMETICO\t%s\n", yytext); }

"("         { printf("PUNTUACION\t%s\n", yytext); }
")"         { printf("PUNTUACION\t%s\n", yytext); }
"{"         { printf("PUNTUACION\t%s\n", yytext); }
"}"         { printf("PUNTUACION\t%s\n", yytext); }
";"         { printf("PUNTUACION\t%s\n", yytext); }
"="         { printf("PUNTUACION\t%s\n", yytext); }

[ \t\n]+    { /* espacio en blanco, se ignora */ }
.           { printf("ERROR_LEXICO\tsimbolo no reconocido: %s\n", yytext); }

%%

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("ERROR_LEXICO\tno se especifico un archivo de entrada\n");
        return 1;
    }
    yyin = fopen(argv[1], "r");
    if (yyin == NULL) {
        printf("ERROR_LEXICO\tno se pudo abrir el archivo\n");
        return 1;
    }
    yylex();
    fclose(yyin);
    return 0;
}