import pygame
import director
from director import *
from menuInicio import MenuPrincipal

if __name__ == '__main__':
    # iniciamos pygame
    pygame.init()

    # creamos el director de juego 
    director = Director()

    # pillamos la primera escena
    escena = MenuPrincipal(director)

    # la metemos en la pila
    director.apilarEscena(escena)

    # a jugar
    director.ejecutar()

    # cerrar al acabar
    pygame.quit()