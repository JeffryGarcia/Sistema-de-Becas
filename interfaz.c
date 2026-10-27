#include <ctype.h>
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "interfaz.h"

typedef struct
{
    const char *nombre;
    const char *estado;
    const char *detalle;
} EstadoBeca;

typedef struct
{
    const char *titulo;
    const char *mensaje;
} Aviso;

typedef struct
{
    const char *fecha;
    const char *evento;
    const char *detalle;
} FechaClave;

/* Datos de demostracion: reemplazarlos con informacion oficial antes de usarlos. */
static const EstadoBeca estados_becas[] = {
    {"Beca de ejemplo 1", "Abierta", "Periodo y requisitos pendientes de confirmar."},
    {"Beca de ejemplo 2", "Proxima", "Consultar la convocatoria oficial para conocer las fechas."},
    {"Beca de ejemplo 3", "Cerrada", "El periodo de registro de ejemplo ya termino."}
};

static const Aviso avisos[] = {
    {"Revision de documentos", "Verifica que los documentos requeridos esten completos."},
    {"Datos de contacto", "Mantener el correo y telefono actualizados facilita recibir avisos."},
    {"Convocatorias", "Consulta las fuentes oficiales antes de iniciar un tramite."}
};

static const FechaClave fechas_clave[] = {
    {"01/01/2026 (ejemplo)", "Publicacion de convocatoria", "Fecha ilustrativa; confirmar con la institucion."},
    {"01/02/2026 (ejemplo)", "Cierre de registro", "Fecha ilustrativa; confirmar con la institucion."},
    {"01/03/2026 (ejemplo)", "Publicacion de resultados", "Fecha ilustrativa; confirmar con la institucion."}
};

void limpiar_pantalla(void)
{
#ifdef _WIN32
    system("cls");
#else
    system("clear");
#endif
}

void pausa(void)
{
    int caracter;

    printf("\nPresione ENTER para continuar...");
    while ((caracter = getchar()) != '\n' && caracter != EOF)
    {
    }
}

ResultadoLectura leer_opcion(int *opcion)
{
    char buffer[64];
    char *fin;
    long valor;
    size_t longitud;
    int caracter;

    if (fgets(buffer, sizeof(buffer), stdin) == NULL)
    {
        if (ferror(stdin))
        {
            perror("Error al leer la opcion");
            return LECTURA_ERROR;
        }
        return LECTURA_FIN;
    }

    longitud = strlen(buffer);
    if (longitud > 0 && buffer[longitud - 1] == '\n')
    {
        buffer[--longitud] = '\0';
    }
    else if (longitud == sizeof(buffer) - 1)
    {
        caracter = getchar();
        if (caracter != '\n' && caracter != EOF)
        {
            while ((caracter = getchar()) != '\n' && caracter != EOF)
            {
            }
            return LECTURA_INVALIDA;
        }
        if (caracter == EOF && ferror(stdin))
        {
            perror("Error al leer la opcion");
            return LECTURA_ERROR;
        }
    }

    errno = 0;
    valor = strtol(buffer, &fin, 10);
    while (isspace((unsigned char)*fin))
    {
        fin++;
    }

    if (opcion == NULL || buffer == fin || *fin != '\0' ||
        errno == ERANGE || valor < INT_MIN || valor > INT_MAX)
    {
        return LECTURA_INVALIDA;
    }

    *opcion = (int)valor;
    return LECTURA_OK;
}

void mostrar_menu_principal(void)
{
    limpiar_pantalla();
    printf("==========================================\n");
    printf("          SISTEMA DE BECAS\n");
    printf("==========================================\n");
    printf("  1. Consultar estado general de becas\n");
    printf("  2. Ver avisos\n");
    printf("  3. Ver fechas clave\n");
    printf("  0. Salir\n");
    printf("------------------------------------------\n");
    printf("Seleccione una opcion: ");
}

void menu_estado_becas(void)
{
    size_t i;

    limpiar_pantalla();
    printf("=== ESTADO GENERAL DE BECAS ===\n");
    printf("AVISO: la siguiente informacion es de demostracion, no oficial.\n\n");

    for (i = 0; i < sizeof(estados_becas) / sizeof(estados_becas[0]); i++)
    {
        printf("%u. %s\n", (unsigned int)(i + 1), estados_becas[i].nombre);
        printf("   Estado: %s\n", estados_becas[i].estado);
        printf("   %s\n\n", estados_becas[i].detalle);
    }

    pausa();
}

void menu_avisos(void)
{
    size_t i;

    limpiar_pantalla();
    printf("=== AVISOS ===\n");
    printf("AVISO: estos mensajes son ejemplos editables.\n\n");

    for (i = 0; i < sizeof(avisos) / sizeof(avisos[0]); i++)
    {
        printf("%u. %s\n", (unsigned int)(i + 1), avisos[i].titulo);
        printf("   %s\n\n", avisos[i].mensaje);
    }

    pausa();
}

void menu_fechas_clave(void)
{
    size_t i;

    limpiar_pantalla();
    printf("=== FECHAS CLAVE ===\n");
    printf("AVISO: las fechas son ejemplos; confirma las fechas oficiales.\n\n");

    for (i = 0; i < sizeof(fechas_clave) / sizeof(fechas_clave[0]); i++)
    {
        printf("%s - %s\n", fechas_clave[i].fecha, fechas_clave[i].evento);
        printf("   %s\n\n", fechas_clave[i].detalle);
    }

    pausa();
}
