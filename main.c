#include <stdio.h>
#include "interfaz.h"

int main(void)
{
    int opcion;
    ResultadoLectura resultado;

    for (;;)
    {
        mostrar_menu_principal();

        resultado = leer_opcion(&opcion);
        if (resultado == LECTURA_FIN)
        {
            printf("\nFin de la entrada. Hasta pronto!\n");
            break;
        }
        if (resultado == LECTURA_ERROR)
        {
            return 1;
        }
        if (resultado == LECTURA_INVALIDA)
        {
            printf("\nEntrada invalida. Escriba un numero del menu.\n");
            pausa();
            continue;
        }

        switch (opcion)
        {
        case 1:
            menu_estado_becas();
            break;
        case 2:
            menu_avisos();
            break;
        case 3:
            menu_fechas_clave();
            break;
        case 0:
            printf("\nHasta pronto!\n");
            return 0;
        default:
            printf("\nOpcion invalida. Intente de nuevo.\n");
            pausa();
        }
    }

    return 0;
}
