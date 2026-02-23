import pygame
import director
from director import *
from menuInicio import MenuPrincipal

if __name__ == '__main__':
    # Inicializamos la librería de pygame
    pygame.init()

    # Creamos el director
    director = Director()

    # Creamos la escena inicial
    escena = MenuPrincipal(director)

    # Le decimos al director que apile esta escena
    director.apilarEscena(escena)

    # Y ejecutamos el juego
    director.ejecutar()

    # Cuando se termine la ejecución, finaliza la librería
    pygame.quit()