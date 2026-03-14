import pygame
import os
from pygame.locals import *
from escena import *
from gestorAudio import GestorAudio, VOL_MUSICA

# rutas para el icono de pausa
HOME = os.path.dirname(__file__)
ASSESTS_FILE = os.path.join(HOME, "..", "assets")
GRAPHICS_FILE = os.path.join(ASSESTS_FILE, "graphics")
PAUSE_FILE = os.path.join(GRAPHICS_FILE, "user_interface", "pause_menu")
ICONO = os.path.join(PAUSE_FILE, "pause.png")
MARCO_BASE = os.path.join(PAUSE_FILE, "marco_base.png")
MARCO_HOVER = os.path.join(PAUSE_FILE, "marco_hover.png")

class MenuPausa(Escena):

    def __init__(self, director):
        Escena.__init__(self, director)
        from menuInicio import BotonEstilizado, PanelGUI
        self.audio = GestorAudio() # Audio

        class PanelPausaGUI(PanelGUI):
            def __init__(self, menu):
                super().__init__()
                from menuInicio import FONT_FILE
                self.fuente_titulo = pygame.font.Font(FONT_FILE, 40)
                self.titulo = self.fuente_titulo.render("PAUSA", True, (255, 215, 0))
                self.sombra = self.fuente_titulo.render("PAUSA", True, (0, 0, 0))
                self.titulo_rect = self.titulo.get_rect(center=(ANCHO//2, 180))

                btn_continuar = BotonEstilizado("CONTINUAR", ANCHO//2, 380, menu.reanudarJuego)
                btn_inicio = BotonEstilizado("INICIO", ANCHO//2, 470, menu.volverInicio)
                self.elementosGUI.extend([btn_continuar, btn_inicio])

            def dibujar(self, pantalla):
                pantalla.blit(self.sombra, (self.titulo_rect.x + 5, self.titulo_rect.y + 5))
                pantalla.blit(self.titulo, self.titulo_rect)
                super().dibujar(pantalla)

        self.panel = PanelPausaGUI(self)
    
    def eventos(self, lista_eventos):
        for evento in lista_eventos:
            if evento.type == KEYDOWN and evento.key == K_ESCAPE:
                self.audio.reproducir_sonido("click_menu_fw", self.audio.canal_ui)
                self.reanudarJuego()
            if evento.type == pygame.QUIT:
                self.director.salirPrograma()
                
        self.panel.eventos(lista_eventos)

    
    def update(self, tiempo_pasado):
        return
    
    def dibujar(self, pantalla):
        if len(self.director.pila) >= 2:
            escena_anterior = self.director.pila[-2]
            escena_anterior.dibujar(pantalla)
        
        overlay = pygame.Surface((ANCHO, ALTO))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        pantalla.blit(overlay, (0, 0))

        self.panel.dibujar(pantalla)

    def reanudarJuego(self):
        self.audio.reproducir_sonido("click_menu_fw", self.audio.canal_ui)
        self.audio.cambiar_volumen_musica(VOL_MUSICA)
        self.director.salirEscena()

    def volverInicio(self):
        from menuInicio import MenuPrincipal
        self.audio.reproducir_sonido("click_menu_bw", self.audio.canal_ui)
        self.audio.detener_musica(fadeout = 0)
        self.director.cambiarEscena(MenuPrincipal(self.director))    