import pygame
import os
from escena import Escena, ANCHO, ALTO
from gestorAudio import GestorAudio

class EscenaDialogo(Escena):
    #patrón Estado: esta escena apílase sobre o xogo para mostrar diálogos, destruíndose ao terminar de ler
    def __init__(self, director, textos, voz="voz_narrador", callback_fin=None, color_texto=(240, 240, 240), fondo_negro=False, color_fondo_caja=(40, 40, 60), color_borde_caja=None):
        super().__init__(director)
        self.audio = GestorAudio()
        self.textos = textos
        self.indice_texto = 0
        self.voz = voz
        self.caracter_anterior = 0
        self.callback_fin = callback_fin

        self.color_texto = color_texto
        self.fondo_negro = fondo_negro

        self.color_fondo_caja = color_fondo_caja
        self.color_borde_caja = color_borde_caja
        
        HOME = os.path.dirname(__file__)
        FONT_FILE = os.path.join(HOME, "..", "assets", "fonts", "PressStart2P-Regular.ttf")
        self.fuente = pygame.font.Font(FONT_FILE, 14)
        
        #animación de escritura
        self.caracteres_mostrados = 0
        self.velocidad_escritura = 0.1 # velocidade algo mais lenta
        
        #dimensión caixa de texto
        self.caja_rect = pygame.Rect(40, ALTO - 120, ANCHO - 80, 100)
        self.espazamento_linas = 8 #espazo extra entre liñas de texto

    def update(self, tiempo_pasado):
        #se rematamos de ler, non actualizamos nada
        if self.indice_texto >= len(self.textos):
            return
        
        texto_actual = self.textos[self.indice_texto]
        
        if self.caracteres_mostrados < len(texto_actual):
            self.caracteres_mostrados += self.velocidad_escritura * tiempo_pasado

            #efecto de son cada par de letras
            caracteres_visibles = int(self.caracteres_mostrados) # caracteres_visibles é agora un int, co que podemos traballar
            if caracteres_visibles > self.caracter_anterior and caracteres_visibles <= len(texto_actual):
                caracter_actual = texto_actual[caracteres_visibles - 1]
                if caracter_actual != " " and caracteres_visibles % 2 == 0:
                    self.audio.canal_texto.stop()
                    self.audio.reproducir_sonido(self.voz, self.audio.canal_texto) # se reproduce a voz indicada no init
            self.caracter_anterior = caracteres_visibles

    def eventos(self, lista_eventos):
        for evento in lista_eventos:
            if evento.type == pygame.KEYDOWN:
                
                if evento.key == pygame.K_ESCAPE:
                    self.director.salirEscena()
                    return 
                if evento.key == pygame.K_SPACE:
                    if self.indice_texto >= len(self.textos):
                        return

                    texto_actual = self.textos[self.indice_texto]
                    
                    if self.caracteres_mostrados < len(texto_actual):
                        self.caracteres_mostrados = len(texto_actual)
                    else:
                        self.indice_texto += 1
                        self.caracteres_mostrados = 0
                        self.caracter_anterior = 0
                        
                        if self.indice_texto >= len(self.textos):
                            self.director.salirEscena() 
                            if self.callback_fin:
                                self.callback_fin()    
                                
    def envolver_texto(self, texto, max_ancho):
        palabras = texto.split(' ')
        linas = []
        lina_actual = ""
        
        for palabra in palabras:
            proba_lina = lina_actual + palabra + " " if lina_actual else palabra + " "
            #comproba se a liña entra na caixa
            if self.fuente.size(proba_lina)[0] <= max_ancho:
                lina_actual = proba_lina
            else:
                if lina_actual:
                    linas.append(lina_actual.rstrip())
                lina_actual = palabra + " "
        
        if lina_actual:
            linas.append(lina_actual.rstrip())
            
        return linas

    def dibujar(self, pantalla):
        #sistema anti-bucles a proba de fallos: debuxa a escena xusto debaixo desta na pila
        #se nos piden fondo negro, tapamos todo o xogo
        if self.fondo_negro:
            pantalla.fill((0, 0, 0))
        else:
            #debuxado normal: debuxamos o que hai debaixo na pila
            if self in self.director.pila:
                indice_actual = self.director.pila.index(self)
                if indice_actual > 0:
                    self.director.pila[indice_actual - 1].dibujar(pantalla)

        #se rematamos non se debuxa caixa de texto
        if self.indice_texto >= len(self.textos):
            return

        #debuxamos caixa do diálogo
        pygame.draw.rect(pantalla, self.color_fondo_caja, self.caja_rect, border_radius=10)

        #se o fondo é negro, ponemos borde vermello á caixa para máis terror; senón, amarelo
        if self.color_borde_caja is not None:
            color_borde = self.color_borde_caja
        else:
            color_borde = (150, 0, 0) if self.fondo_negro else (255, 215, 0)
        pygame.draw.rect(pantalla, color_borde, self.caja_rect, 3, border_radius=10)

        #preparamos o texto actual
        texto_actual = self.textos[self.indice_texto]
        max_ancho_texto = self.caja_rect.width - 40
        
        #dividimos o texto en liñas que caiban na caixa (e respectamos os \n manuais)
        linas_totais = []
        for lina_manual in texto_actual.split('\n'):
            linas_totais.extend(self.envolver_texto(lina_manual, max_ancho_texto))
            
        #debuxamos o texto progresivamente liña por liña
        caracteres_restantes = int(self.caracteres_mostrados)
        y_offset = 0
        
        for lina in linas_totais:
            if caracteres_restantes <= 0:
                break
                
            #collemos só a cantidade de caracteres que tocan debuxar nesta liña
            texto_lina = lina[:caracteres_restantes]
            caracteres_restantes -= len(lina)
            
            #usamos self.color_texto en lugar de blanco fixo
            render = self.fuente.render(texto_lina, True, self.color_texto)
            pantalla.blit(render, (self.caja_rect.x + 20, self.caja_rect.y + 20 + y_offset))
            y_offset += self.fuente.get_height() + self.espazamento_linas
        
        #indicador tecla para pasar o diálogo
        if self.caracteres_mostrados >= len(texto_actual):
            ind_render = self.fuente.render("ESPACIO", True, (200, 200, 200))
            pantalla.blit(ind_render, (self.caja_rect.right - 120, self.caja_rect.bottom - 25))