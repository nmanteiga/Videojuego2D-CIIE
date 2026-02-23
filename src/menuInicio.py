import pygame
from escena import Escena, ANCHO, ALTO
from game import Juego, FONDO_IMG

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

        self.fuente = pygame.font.SysFont("Calibri", 30, bold=True)
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
        
        self.fondo = pygame.image.load(FONDO_IMG).convert_alpha()
        self.fondo = pygame.transform.scale(self.fondo, (ANCHO, ALTO))
        
        self.fuente_titulo = pygame.font.SysFont("Impact", 90)
        self.titulo = self.fuente_titulo.render("SCAPE FROM FIC", True, (255, 215, 0))
        self.sombra = self.fuente_titulo.render("SCAPE FROM FIC", True, (0, 0, 0))
        self.titulo_rect = self.titulo.get_rect(center=(ANCHO//2, 180))

        btn_jugar = BotonEstilizado("JUGAR", ANCHO//2, 380, self.menu.ejecutarJuego)
        btn_salir = BotonEstilizado("SALIR", ANCHO//2, 470, self.menu.salirPrograma)
        
        self.elementosGUI.append(btn_jugar)
        self.elementosGUI.append(btn_salir)

    def dibujar(self, pantalla):
        pantalla.blit(self.fondo, (0, 0))
        
        overlay = pygame.Surface((ANCHO, ALTO))
        overlay.set_alpha(120) 
        overlay.fill((0, 0, 0))
        pantalla.blit(overlay, (0, 0))
        
        pantalla.blit(self.sombra, (self.titulo_rect.x + 5, self.titulo_rect.y + 5))
        pantalla.blit(self.titulo, self.titulo_rect)
        
        super().dibujar(pantalla)


class MenuPrincipal(Escena):
    def __init__(self, director):
        super().__init__(director)
        self.listaPaneles = {}
        self.listaPaneles['INICIAL'] = PanelInicialGUI(self)
        self.panelActual = 'INICIAL'

    def update(self, tiempo_pasado):
        pass

    def eventos(self, lista_eventos):
        for evento in lista_eventos:
            if evento.type == pygame.QUIT:
                self.director.salirPrograma()
        self.listaPaneles[self.panelActual].eventos(lista_eventos)

    def dibujar(self, pantalla):
        self.listaPaneles[self.panelActual].dibujar(pantalla)

    def ejecutarJuego(self):
        juego = Juego(self.director)
        self.director.cambiarEscena(juego) 

    def salirPrograma(self):
        self.director.salirPrograma()