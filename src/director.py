import pygame
import sys
# import escena
from escena import *
from pygame.locals import *


class Director():

    def __init__(self):
        # enganchamos la ventana del juego
        self.screen = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption("Scape From FIC")

        # aquí guardamos las escenas
        self.pila = []

        # flag para saber cuando cerrar
        self.salir_escena = False
        
        # relojito para los fps
        self.reloj = pygame.time.Clock()


    def bucle(self, escena):
        self.salir_escena = False

        pygame.event.clear()
        
        while not self.salir_escena:
            tiempo_pasado = self.reloj.tick(60)
            escena.eventos(pygame.event.get())

            if self.salir_escena:
                break

            escena.update(tiempo_pasado)
            escena.dibujar(self.screen)
            pygame.display.flip()


    def ejecutar(self):
        # mientras tengamos escenas cargadas vamos tirando
        while (len(self.pila)>0):

            # cogemos la que está más arriba 
            escena = self.pila[len(self.pila)-1]
            self.bucle(escena)


    def salirEscena(self):
        self.salir_escena = True

        # hacemos pop de la lista si hay algo
        if (len(self.pila)>0):
            self.pila.pop()

    def salirPrograma(self):
        # se vacía todo 
        self.pila = []
        self.salir_escena = True

    def cambiarEscena(self, escena):
        self.salirEscena()

        # metemos la nueva
        self.pila.append(escena)

    def apilarEscena(self, escena):
        self.salir_escena = True
        
        # metemos la escena pasada por encima de la que hay
        self.pila.append(escena)