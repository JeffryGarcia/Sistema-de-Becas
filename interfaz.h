#ifndef INTERFAZ_H
#define INTERFAZ_H

typedef enum
{
    LECTURA_ERROR = -2,
    LECTURA_FIN = -1,
    LECTURA_INVALIDA = 0,
    LECTURA_OK = 1
} ResultadoLectura;

void limpiar_pantalla(void);
void pausa(void);
ResultadoLectura leer_opcion(int *opcion);

void mostrar_menu_principal(void);
void menu_estado_becas(void);
void menu_avisos(void);
void menu_fechas_clave(void);

#endif