import pygame
import os
from escena import Escena, ANCHO, ALTO
from gestorAudio import GestorAudio

class EscenaDialogo(Escena):
    #Patrón Estado: esta escena apílase sobre o xogo para mostrar diálogos, destruíndose ao terminar de ler
    def __init__(self, director, textos, callback_fin=None):
        super().__init__(director)
        self.audio = GestorAudio()
        self.textos = textos
        self.indice_texto = 0
        self.callback_fin = callback_fin
        
        HOME = os.path.dirname(__file__)
        FONT_FILE = os.path.join(HOME, "..", "assets", "fonts", "PressStart2P-Regular.ttf")
        self.fuente = pygame.font.Font(FONT_FILE, 14)
        
        #animación de escritura
        self.caracteres_mostrados = 0
        self.velocidad_escritura = 0.5
        
        #dimensión caixa de texto
        self.caja_rect = pygame.Rect(40, ALTO - 120, ANCHO - 80, 100)

    def update(self, tiempo_pasado):
        #se rematamos de ler, non actualizamos nada
        if self.indice_texto >= len(self.textos):
            return

        texto_actual = self.textos[self.indice_texto]
        if self.caracteres_mostrados < len(texto_actual):
            self.caracteres_mostrados += self.velocidad_escritura * tiempo_pasado
            
            #efecto de son cada par de letras
            if int(self.caracteres_mostrados) % 3 == 0 and not self.audio.canal_texto.get_busy():
                self.audio.reproducir_sonido("voz_michel", self.audio.canal_texto)

    def eventos(self, lista_eventos):
        for evento in lista_eventos:
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_SPACE:
                #doble check de seguridade por se ocorre un doble clic
                if self.indice_texto >= len(self.textos):
                    return

                texto_actual = self.textos[self.indice_texto]
                
                #se non rematou de escribir, o autocompleta de golpe
                if self.caracteres_mostrados < len(texto_actual):
                    self.caracteres_mostrados = len(texto_actual)
                else:
                    #se remata pasa ao seguinte
                    self.indice_texto += 1
                    self.caracteres_mostrados = 0
                    
                    #saímos se non máis textos
                    if self.indice_texto >= len(self.textos):
                        self.director.salirEscena() #matamos o diálogo anterior
                        if self.callback_fin:
                            self.callback_fin()     #creamos o novo

    def dibujar(self, pantalla):
        #debuxamos o fondo do xogo
        if len(self.director.pila) >= 2:
            self.director.pila[-2].dibujar(pantalla)

        #se rematamos non se debuxa caixa de texto
        if self.indice_texto >= len(self.textos):
            return

        #debuxamos caixa do diálogo
        pygame.draw.rect(pantalla, (40, 40, 60), self.caja_rect, border_radius=10)
        pygame.draw.rect(pantalla, (255, 215, 0), self.caja_rect, 3, border_radius=10)

        #debuxamos o texto ata onde foi animado
        texto_actual = self.textos[self.indice_texto]
        texto_visible = texto_actual[:int(self.caracteres_mostrados)]
        
        render = self.fuente.render(texto_visible, True, (240, 240, 240))
        pantalla.blit(render, (self.caja_rect.x + 20, self.caja_rect.y + 20))
        
        #indicador tecla para pasar o diálogo
        if self.caracteres_mostrados >= len(texto_actual):
            ind_render = self.fuente.render("ESPACIO >", True, (200, 200, 200))
            pantalla.blit(ind_render, (self.caja_rect.right - 120, self.caja_rect.bottom - 25))