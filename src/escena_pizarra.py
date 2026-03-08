import pygame
import os
from escena import Escena, ANCHO, ALTO
from gestorAudio import GestorAudio

# Colores estilo tiza
COLOR_PIZARRA = (43, 83, 41)       
COLOR_MARCO = (92, 64, 51)         
COLOR_TIZA = (240, 240, 240)       
COLOR_HOVER = (200, 200, 200)      
COLOR_CORRECTO = (100, 255, 100)   
COLOR_INCORRECTO = (255, 100, 100) 

class OpcionTest:
    """
    Patrón Componente: Cada opción gestiona su propio estado, lógica (update) y renderizado (dibujar).
    """
    def __init__(self, letra, texto, y, fuente, es_correcta=False):
        self.letra = letra
        self.texto_str = texto
        self.es_correcta = es_correcta
        self.fuente = fuente
        # Área clicable de la opción
        self.rect = pygame.Rect(150, y, 500, 40)
        self.estado = "NORMAL" # Estados: NORMAL, HOVER, CORRECTO, INCORRECTO

    def update(self, raton_pos):
        # Si ya se ha respondido, no cambiamos el estado al pasar el ratón
        if self.estado in ["CORRECTO", "INCORRECTO"]:
            return 
            
        if self.rect.collidepoint(raton_pos):
            self.estado = "HOVER"
        else:
            self.estado = "NORMAL"

    def dibujar(self, pantalla):
        if self.estado == "NORMAL": color = COLOR_TIZA
        elif self.estado == "HOVER": color = COLOR_HOVER
        elif self.estado == "CORRECTO": color = COLOR_CORRECTO
        elif self.estado == "INCORRECTO": color = COLOR_INCORRECTO

        texto_render = self.fuente.render(f"{self.letra}) {self.texto_str}", True, color)
        pantalla.blit(texto_render, (self.rect.x, self.rect.y))

class EscenaPizarra(Escena):
    # 1. Añadimos el parámetro callback_acierto (por defecto None)
    def __init__(self, director, callback_acierto=None):
        super().__init__(director)
        self.callback_acierto = callback_acierto # Lo guardamos
        self.audio = GestorAudio()
        
        # Cargamos la fuente de tu proyecto
        HOME = os.path.dirname(__file__)
        FONT_FILE = os.path.join(HOME, "..", "assets", "fonts", "PressStart2P-Regular.ttf")
        self.fuente_titulo = pygame.font.Font(FONT_FILE, 20)
        self.fuente_opciones = pygame.font.Font(FONT_FILE, 16)
        
        self.pregunta = "¿Quién inventó Pygame?"
        
        # Patrón Componente: Instanciamos las opciones
        self.opciones = [
            OpcionTest("A", "Guido van Rossum", 250, self.fuente_opciones, False),
            OpcionTest("B", "Pete Shinners", 310, self.fuente_opciones, True),
            OpcionTest("C", "Markus Persson", 370, self.fuente_opciones, False),
            OpcionTest("D", "Bill Gates", 430, self.fuente_opciones, False)
        ]
        
        self.respondido = False
        self.tiempo_salida = 0 
        self.pizarra_rect = pygame.Rect(100, 100, ANCHO - 200, ALTO - 200)

    def eventos(self, lista_eventos):
        # Si ya ha respondido, ignoramos los clics y teclas para que no responda dos veces
        if self.respondido:
            return 

        for evento in lista_eventos:
            # 1. Control por Ratón
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                for opcion in self.opciones:
                    if opcion.estado == "HOVER":
                        self.evaluar_respuesta(opcion)
            
            # 2. Control por Teclado
            if evento.type == pygame.KEYDOWN:
                # Salir de la escena con ESC
                if evento.key == pygame.K_ESCAPE:
                    self.audio.reproducir_sonido("click_menu_bw", self.audio.canal_ui)
                    self.director.salirEscena()
                
                # --- NUEVO: Atajos A, B, C, D ---
                # self.opciones[0] es la A, self.opciones[1] es la B, etc.
                elif evento.key == pygame.K_a:
                    self.evaluar_respuesta(self.opciones[0])
                elif evento.key == pygame.K_b:
                    self.evaluar_respuesta(self.opciones[1])
                elif evento.key == pygame.K_c:
                    self.evaluar_respuesta(self.opciones[2])
                elif evento.key == pygame.K_d:
                    self.evaluar_respuesta(self.opciones[3])

    def evaluar_respuesta(self, opcion_seleccionada):
        self.respondido = True
        if opcion_seleccionada.es_correcta:
            opcion_seleccionada.estado = "CORRECTO"
            self.audio.reproducir_sonido("campana", self.audio.canal_ui)

            # --- NUEVO: Si acertó, ejecutamos la función que nos pasaron ---
            if self.callback_acierto:
                self.callback_acierto()
        else:
            opcion_seleccionada.estado = "INCORRECTO"
            self.audio.reproducir_sonido("click_menu_bw", self.audio.canal_ui) 
            # Mostramos la correcta para que aprenda el jugador
            for op in self.opciones:
                if op.es_correcta:
                    op.estado = "CORRECTO"
        
        self.tiempo_salida = pygame.time.get_ticks()

    def update(self, tiempo_pasado):
        raton_pos = pygame.mouse.get_pos()
        for opcion in self.opciones:
            opcion.update(raton_pos)

        # Si ya respondió, esperamos 2 segundos y sacamos la escena de la pila
        if self.respondido and pygame.time.get_ticks() - self.tiempo_salida > 2000:
            self.director.salirEscena()

    def dibujar(self, pantalla):
        # Dibujamos la escena de debajo (el juego) para que se vea de fondo
        if len(self.director.pila) >= 2:
            escena_anterior = self.director.pila[-2]
            escena_anterior.dibujar(pantalla)

        # Filtro oscuro semitransparente (típico de menús 2D)
        overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        pantalla.blit(overlay, (0, 0))

        # Dibujar la Pizarra (Marco y Fondo)
        pygame.draw.rect(pantalla, COLOR_MARCO, self.pizarra_rect.inflate(20, 20), border_radius=10)
        pygame.draw.rect(pantalla, COLOR_PIZARRA, self.pizarra_rect)

        # Dibujar Título centrado
        titulo_render = self.fuente_titulo.render(self.pregunta, True, COLOR_TIZA)
        titulo_x = self.pizarra_rect.centerx - (titulo_render.get_width() // 2)
        pantalla.blit(titulo_render, (titulo_x, 150))

        # Delegar el dibujado a cada componente
        for opcion in self.opciones:
            opcion.dibujar(pantalla)