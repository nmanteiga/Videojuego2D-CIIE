import pygame
import director
from director import *
from game import Juego # (Sólo mientras no haya menú de inicio)

if __name__ == '__main__':
    # Inicializamos la librería de pygame
    pygame.init()

    # Creamos el director
    director = Director()

    # Creamos la escena inicial
    escena = Juego(director)

    # Le decimos al director que apile esta escena
    director.apilarEscena(escena)

    # Y ejecutamos el juego
    director.ejecutar()

    # Cuando se termine la ejecución, finaliza la librería
    pygame.quit()