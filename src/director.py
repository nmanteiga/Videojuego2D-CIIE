import pygame
import sys
# import escena
from escena import *
from pygame.locals import *


class Director():

    def __init__(self):
        # Inicializamos la pantalla y el modo gráfico
        self.screen = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption("Scape From FIC")

        # Pila de escenas
        self.pila = []

        # Flag que nos indica cuando quieren salir de la escena
        self.salir_escena = False
        
        # Reloj
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
        # Mientras haya escenas en la pila, ejecutaremos la de arriba
        while (len(self.pila)>0):

            # Se coge la escena a ejecutar como la que este en la cima de la pila
            escena = self.pila[len(self.pila)-1]

            # Ejecutamos el bucle de eventos hasta que termine la escena
            self.bucle(escena)


    def salirEscena(self):
        # Indicamos en el flag que se quiere salir de la escena
        self.salir_escena = True

        # Eliminamos la escena actual de la pila (si la hay)
        if (len(self.pila)>0):
            self.pila.pop()

    def salirPrograma(self):
        # Vaciamos la lista de escenas pendientes
        self.pila = []
        self.salir_escena = True

    def cambiarEscena(self, escena):
        self.salirEscena()

        # Ponemos la escena pasada en la cima de la pila
        self.pila.append(escena)

    def apilarEscena(self, escena):
        self.salir_escena = True
        
        # Ponemos la escena pasada en la cima de la pila
        #  (por encima de la actual)
        self.pila.append(escena)