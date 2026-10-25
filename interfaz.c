#include <stdio.h>
#include <stdlib.h>
#include "interfaz.h"

void limpiar_pantalla(void) {
#ifdef _WIN32
    system("cls");
#else
    system("clear");
#endif
}

void pausa(void) {
    printf("\nPresione ENTER para continuar...");
    getchar();
}

/* Lee una opción de forma segura (evita que el programa se cicle si escriben letras) */
int leer_opcion(void) {
    char buffer[32];
    int opcion;

    if (fgets(buffer, sizeof(buffer), stdin) == NULL) {
        return -1;
    }
    if (sscanf(buffer, "%d", &opcion) != 1) {
        return -1;
    }
    return opcion;
}

void mostrar_menu_principal(void) {
    limpiar_pantalla();
    printf("==========================================\n");
    printf("          SISTEMA DE BECAS\n");
    printf("==========================================\n");
    printf("  1. Consultar estado de becas\n");
    printf("  2. Ver avisos\n");
    printf("  3. Ver fechas clave\n");
    printf("  0. Salir\n");
    printf("------------------------------------------\n");
    printf("Seleccione una opcion: ");
}

void menu_estado_becas(void) {
    limpiar_pantalla();
    printf("=== ESTADO DE BECAS ===\n");
    printf("(Pendiente de implementar)\n");
    pausa();
}

void menu_avisos(void) {
    limpiar_pantalla();
    printf("=== AVISOS ===\n");
    printf("(Pendiente de implementar)\n");
    pausa();
}

void menu_fechas_clave(void) {
    limpiar_pantalla();
    printf("=== FECHAS CLAVE ===\n");
    printf("(Pendiente de implementar)\n");
    pausa();
}