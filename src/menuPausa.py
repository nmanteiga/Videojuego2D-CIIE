import pygame
import os
from pygame.locals import *
from escena import *

# Rutas para el icono de pausa
HOME = os.path.dirname(__file__)
ASSESTS_FILE = os.path.join(HOME, "..", "assets")
GRAPHICS_FILE = os.path.join(ASSESTS_FILE, "graphics")
PAUSE_FILE = os.path.join(GRAPHICS_FILE, "user_interface", "pause_menu")
ICONO = os.path.join(PAUSE_FILE, "pause.png")
MARCO_BASE = os.path.join(PAUSE_FILE, "marco_base.png")
MARCO_HOVER = os.path.join(PAUSE_FILE, "marco_hover.png")

class MenuPausa(Escena):

    def __init__(self, director):
        # Llamamos al constructor de la clase padre
        Escena.__init__(self, director)

        # Icono del menú (de prueba, lo hice en unos cinco minutos)
        self.icono = pygame.image.load(ICONO).convert_alpha()
        self.icono = pygame.transform.scale(self.icono, (64, 64))
        self.icono_rect = self.icono.get_rect(center = (64, 64))

        # Texto del menú
        self.font_texto = pygame.font.SysFont("Calibri", 40, bold = True)
        self.texto = self.font_texto.render("PAUSA", True, (255, 255, 255))
        self.texto_rect = self.texto.get_rect(center = (ANCHO / 2, (ALTO / 2) - 100))

        # Botón de continuar (con otro marco de prueba que hice en otros cinco minutos)
        self.boton_marco_base = pygame.image.load(MARCO_BASE).convert_alpha()
        self.boton_marco_base = pygame.transform.scale(self.boton_marco_base, (320, 100))
        self.boton_marco_hover = pygame.image.load(MARCO_HOVER).convert_alpha()
        self.boton_marco_hover = pygame.transform.scale(self.boton_marco_hover, (320, 100))
        self.boton_rect = self.boton_marco_base.get_rect(center = (ANCHO / 2, (ALTO / 2)))
        self.font_boton = pygame.font.SysFont("Calibri", 45)
        self.texto_boton = self.font_boton.render("CONTINUAR", True, (0, 0, 0))
        self.texto_boton_rect = self.texto_boton.get_rect(center = self.boton_rect.center)
    
    def eventos(self, lista_eventos):
        # Se comprueba si se quiere salir de la escena
        for evento in lista_eventos:

            # Si se quiere salir, se le indica al director
            if evento.type == KEYDOWN:
                if evento.key == K_ESCAPE:
                    self.director.salirEscena()

            # Si se hace click dentro del botón de continuar, también se sale
            if evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1: # Click izquierdo
                    if self.boton_rect.collidepoint(evento.pos): # Si se hace click dentro del botón
                        self.director.salirEscena()
            
            if evento.type == pygame.QUIT:
                self.director.salirPrograma()

    
    def update(self, tiempo_pasado):
        return
    
    def dibujar(self, pantalla):
        # Dibujar la escena anterior (debajo de la actual en la pila), si existe
        if len(self.director.pila) >= 2:
            escena_anterior = self.director.pila[-2]
            escena_anterior.dibujar(pantalla)
        
        # Dibujado del fondo (negro semi-transparente)
        overlay = pygame.Surface((ANCHO, ALTO))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        pantalla.blit(overlay, (0, 0))

        # Dibujado del texto
        pantalla.blit(self.icono, self.icono_rect)
        pantalla.blit(self.texto, self.texto_rect)

        # Dibujado del botón. Primero se detecta si el ratón está encima
        raton_pos = pygame.mouse.get_pos()
        if self.boton_rect.collidepoint(raton_pos):
            pantalla.blit(self.boton_marco_hover, self.boton_rect)
        else:
            pantalla.blit(self.boton_marco_base, self.boton_rect)
        
        pantalla.blit(self.texto_boton, self.texto_boton_rect)
