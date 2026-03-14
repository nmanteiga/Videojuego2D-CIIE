import pygame
import os
from PIL import Image
from escena import Escena, ANCHO, ALTO
from game import Juego, FONDO_IMG, GRAPHICS_FILE
from escena_cinematica_principio import run_cinematics
from gestorAudio import GestorAudio

HOME = os.path.dirname(__file__)
ASSETS_FILE = os.path.join(HOME, "..", "assets")
FONT_FILE = os.path.join(ASSETS_FILE, "fonts", "PressStart2P-Regular.ttf")
MENU_GIF = os.path.join(GRAPHICS_FILE, "ui", "menuInicio.gif")

def cargar_gif(ruta, ancho, alto):
    frames = []
    duraciones = []
    gif = Image.open(ruta)
    
    try:
        while True:
            # Convertir frame a formato pygame
            frame = gif.convert("RGBA")
            frame = frame.resize((ancho, alto), Image.Resampling.LANCZOS)
            data = frame.tobytes()
            superficie = pygame.image.fromstring(data, (ancho, alto), "RGBA")
            frames.append(superficie)
            
            # Obtener duración del frame (en ms)
            duracion = gif.info.get('duration', 100)
            duraciones.append(duracion)
            
            gif.seek(gif.tell() + 1)
    except EOFError:
        pass
    
    return frames, duraciones

#PATRÓN COMPONENTE
class ElementoGUI:
    def __init__(self, rectangulo):
        self.rect = rectangulo

    def posicionEnElemento(self, posicion):
        return self.rect.collidepoint(posicion)

    def dibujar(self, pantalla):
        pass

    def accion(self):
        pass

class BotonEstilizado(ElementoGUI):
    def __init__(self, texto, centro_x, centro_y, accion_callback):
        ancho_boton = 220
        alto_boton = 60
        rect = pygame.Rect(0, 0, ancho_boton, alto_boton)
        rect.center = (centro_x, centro_y)
        super().__init__(rect)
        
        self.accion_callback = accion_callback
        self.texto_str = texto

        self.color_fondo_normal = (40, 40, 60)
        self.color_fondo_hover = (70, 70, 90)
        self.color_borde = (255, 215, 0)   
        self.color_texto = (255, 255, 255)

        self.fuente = pygame.font.Font(FONT_FILE, 16)
        self.texto_render = self.fuente.render(self.texto_str, True, self.color_texto)
        self.texto_rect = self.texto_render.get_rect(center=self.rect.center)

    def dibujar(self, pantalla):
        raton_pos = pygame.mouse.get_pos()
        esta_encima = self.posicionEnElemento(raton_pos)
        
        if esta_encima:
            color_fondo = self.color_fondo_hover
            grosor_borde = 3
        else:
            color_fondo = self.color_fondo_normal
            grosor_borde = 1

        pygame.draw.rect(pantalla, color_fondo, self.rect, border_radius=15)

        pygame.draw.rect(pantalla, self.color_borde, self.rect, grosor_borde, border_radius=15)
            
        pantalla.blit(self.texto_render, self.texto_rect)

    def accion(self):
        self.accion_callback()


#PANELES
class PanelGUI:
    def __init__(self):
        self.elementosGUI = []

    def update(self, tiempo_pasado):
        pass

    def eventos(self, lista_eventos):
        for evento in lista_eventos:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                for elemento in self.elementosGUI:
                    if elemento.posicionEnElemento(evento.pos):
                        elemento.accion()

    def dibujar(self, pantalla):
        for elemento in self.elementosGUI:
            elemento.dibujar(pantalla)

class PanelInicialGUI(PanelGUI):
    def __init__(self, menu):
        super().__init__()
        self.menu = menu
        
        self.frames_fondo, self.duraciones = cargar_gif(MENU_GIF, ANCHO, ALTO)
        self.frame_actual = 0
        self.tiempo_acumulado = 0
        
        btn_jugar = BotonEstilizado("JUGAR", ANCHO//2, 430, self.menu.ejecutarJuego)
        btn_salir = BotonEstilizado("SALIR", ANCHO//2, 510, self.menu.salirPrograma)
        
        self.elementosGUI.append(btn_jugar)
        self.elementosGUI.append(btn_salir)

    def update(self, tiempo_pasado):
        self.tiempo_acumulado += tiempo_pasado
        if self.tiempo_acumulado >= self.duraciones[self.frame_actual]:
            self.tiempo_acumulado = 0
            self.frame_actual = (self.frame_actual + 1) % len(self.frames_fondo)

    def dibujar(self, pantalla):
        pantalla.blit(self.frames_fondo[self.frame_actual], (0, 0))
        super().dibujar(pantalla)


class MenuPrincipal(Escena):
    def __init__(self, director):
        super().__init__(director)
        self.listaPaneles = {}
        self.listaPaneles['INICIAL'] = PanelInicialGUI(self)
        self.panelActual = 'INICIAL'
        self.audio = GestorAudio() # Audio
        self._tiempo_ultimo_click = 0  # Evitar múltiples clicks

        # Música del menú de inicio (temporalmente la de escape):
        self.audio.reproducir_musica("escape")

    def update(self, tiempo_pasado):
        self._tiempo_ultimo_click += tiempo_pasado
        self.listaPaneles[self.panelActual].update(tiempo_pasado)

    def eventos(self, lista_eventos):
        for evento in lista_eventos:
            if evento.type == pygame.QUIT:
                self.director.salirPrograma()
        
        # Solo procesar clicks si ha pasado suficiente tiempo desde el último
        if self._tiempo_ultimo_click >= 300:
            self.listaPaneles[self.panelActual].eventos(lista_eventos)
            if any(e.type == pygame.MOUSEBUTTONDOWN for e in lista_eventos):
                self._tiempo_ultimo_click = 0

    def dibujar(self, pantalla):
        self.listaPaneles[self.panelActual].dibujar(pantalla)

    def ejecutarJuego(self):
        self.audio.reproducir_sonido("click_menu_big", self.audio.canal_ui)
        self.audio.detener_musica(500)
        run_cinematics(self.director.screen)
        juego = Juego(self.director)
        self.director.cambiarEscena(juego) 

    def salirPrograma(self):
        self.director.salirPrograma()