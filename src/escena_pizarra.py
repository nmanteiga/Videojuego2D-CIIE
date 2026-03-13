import pygame
import os
from escena import Escena, ANCHO, ALTO
from gestorAudio import GestorAudio

COLOR_PIZARRA = (43, 83, 41)       
COLOR_MARCO = (92, 64, 51)         
COLOR_TIZA = (240, 240, 240)       
COLOR_HOVER = (200, 200, 200)      
COLOR_CORRECTO = (100, 255, 100)   
COLOR_INCORRECTO = (255, 100, 100) 

#para o texto longo, esta función axusta o texto para que se divida en varias liñas se supera un ancho máximo, evitando que se saia da pizarra
def envolver_texto(texto, fuente, max_ancho):
    palabras = texto.split(' ')
    lineas = []
    linea_actual = ""
    
    for palabra in palabras:
        test_linea = linea_actual + palabra + " "
        #se a liña coa nova palabra cabe, engadímola
        if fuente.size(test_linea)[0] <= max_ancho:
            linea_actual = test_linea
        else:
            #se non cabe, gardamos a liña actual e empezamos unha nova
            if linea_actual == "": #por se unha soa palabra é xigante
                lineas.append(palabra)
                linea_actual = ""
            else:
                lineas.append(linea_actual)
                linea_actual = palabra + " "
                
    if linea_actual:
        lineas.append(linea_actual)
    return lineas

class OpcionTest:
    #patrón Componente: cada opción xestiona o seu propio estado, update e dibujar.
    def __init__(self, letra, texto, y, fuente, max_ancho, es_correcta=False):
        self.letra = letra
        self.texto_str = texto
        self.es_correcta = es_correcta
        self.fuente = fuente
        self.max_ancho = max_ancho

        #envolvemos o texto da opción por se é moi longo
        self.lineas_texto = envolver_texto(f"{self.letra}) {self.texto_str}", self.fuente, self.max_ancho)
        
        #o alto do rectángulo depende de cantas liñas teña
        alto_rect = len(self.lineas_texto) * 20 + 10

        #área clic co rato
        self.rect = pygame.Rect(150, y, 500, alto_rect)
        self.estado = "NORMAL" #NORMAL, HOVER, CORRECTO, INCORRECTO

    def update(self, raton_pos):
        #se xa respondido, non se cambia estado co rato
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

        #debuxamos liña por liña
        for i, linea in enumerate(self.lineas_texto):
            texto_render = self.fuente.render(linea, True, color)
            # i * 20 fai que a seguinte liña baixe 20 píxeles respecto á anterior
            pantalla.blit(texto_render, (self.rect.x, self.rect.y + (i * 20)))
class EscenaPizarra(Escena):
    def __init__(self, director, vidas_actuales, callback_acierto=None, callback_gameover=None, callback_restar_vida=None, callback_penalizacion=None):
        super().__init__(director)
        self.callback_acierto = callback_acierto
        self.callback_gameover = callback_gameover
        self.callback_restar_vida = callback_restar_vida
        self.callback_penalizacion = callback_penalizacion
        self.audio = GestorAudio()

        self.vidas = vidas_actuales #usamos as vidas que nos di o game.py, para manter un rexistro correcto
        self.indice_pregunta = 0

        #banco de preguntas
        self.banco_preguntas = [
            #pregunta pygame
            {
                "pregunta": "¿Quién inventó Pygame?",
                "opciones": [
                    ("A", "Guido van Rossum", False),
                    ("B", "Pete Shinners", True),
                    ("C", "Markus Persson", False),
                    ("D", "Bill Gates", False)
                ]
            },
            #pregunta doom
            {
                "pregunta": "¿Cuál es el juego que puedo jugar en un test de embarazo, e incluso, en una bacteria?",
                "opciones": [
                    ("A", "Tetris", False),
                    ("B", "Portal", False),
                    ("C", "Minecraft", False),
                    ("D", "Doom", True)
                ]
            },
            #pregunta tortilla
            {
                "pregunta": "¿Qué pasó el 20 de noviembre de 2025 en la FIC?",
                "opciones": [
                    ("A", "Llovió y no hubo goteras", False),
                    ("B", "Pues nada, ¿qué iba a pasar?", False),
                    ("C", "Falsa alarma de bomba", True),
                    ("D", "Michel hizo una fiesta en la cafetería", False)
                ]
            },
            #pregunta ciie
            {
                "pregunta": "¿Qué significan las siglas de CIIE?",
                "opciones": [
                    ("A", "Contornos Inmersivos, Interactivos e de Entretemento", True),
                    ("B", "Contornos Intuitivos, Inclusivos e de Espazamento", False),
                    ("C", "Contratos Influentes, Importantes e Especiais", False),
                    ("D", "No lo sé, lo siento Quique", True)
                ]
            }
        ]
        
        #fonte do texto
        HOME = os.path.dirname(__file__)
        FONT_FILE = os.path.join(HOME, "..", "assets", "fonts", "PressStart2P-Regular.ttf")
        self.fuente_titulo = pygame.font.Font(FONT_FILE, 20)
        self.fuente_opciones = pygame.font.Font(FONT_FILE, 16)
        
        
        self.respondido = False
        self.tiempo_salida = 0
        self.estado_respuesta = None #CORRECTO ou INCORRECTO

        self.pizarra_rect = pygame.Rect(100, 100, ANCHO - 200, ALTO - 200)
        self.cargar_pregunta_actual()

    def cargar_pregunta_actual(self): #crea os obxetos OpcionTest basándose no índice actual
        datos = self.banco_preguntas[self.indice_pregunta]
        self.pregunta = datos["pregunta"]
        self.opciones = []

        #calculamos cantas liñas ocupa a pregunta principal para saber onde empezar a pintar as opcións
        ancho_maximo_texto = self.pizarra_rect.width - 40
        self.lineas_pregunta = envolver_texto(self.pregunta, self.fuente_titulo, ancho_maximo_texto)
        
        alto_ocupado_por_pregunta = len(self.lineas_pregunta) * 25
        
        y_inicial = self.pizarra_rect.y + 40 + alto_ocupado_por_pregunta + 20 
        separacion = 60 # píxeles base de separación
        
        #debuxar as opcións (se unha ocupa moito, empuxará á seguinte cara abaixo)
        y_actual = y_inicial
        for i, (letra, texto, correcta) in enumerate(datos["opciones"]):
            #instaciamos a clase OpcionTest para cada opción, pasando se é correcta ou non
            nova_opcion = OpcionTest(letra, texto, y_actual, self.fuente_opciones, ancho_maximo_texto - 60, correcta)
            self.opciones.append(nova_opcion)

            #sumámoslle a altura que ocupou este botón específico para que o seguinte quede debaixo
            y_actual += nova_opcion.rect.height + 15

    def eventos(self, lista_eventos):
        #se xa houbo resposta, ignoramos los clics y teclas
        if self.respondido:
            return 

        for evento in lista_eventos:
            #control co rato
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                for opcion in self.opciones:
                    if opcion.estado == "HOVER":
                        self.evaluar_respuesta(opcion)
            
            #control por teclado
            if evento.type == pygame.KEYDOWN:
                #saír da escena con ESC
                if evento.key == pygame.K_ESCAPE:
                    self.audio.reproducir_sonido("click_menu_bw", self.audio.canal_ui)
                    self.director.salirEscena()
                
                #pódese responder tamén co teclado (A, B, C, D)
                elif evento.key == pygame.K_a:
                    self.evaluar_respuesta(self.opciones[0])
                elif evento.key == pygame.K_b:
                    self.evaluar_respuesta(self.opciones[1])
                elif evento.key == pygame.K_c:
                    self.evaluar_respuesta(self.opciones[2])
                elif evento.key == pygame.K_d:
                    self.evaluar_respuesta(self.opciones[3])

    def evaluar_respuesta(self, opcion_elegida):
        #marcamos que xa respondeu e gardamos o momento exacto para a espera
        self.respondido = True
        self.tiempo_salida = pygame.time.get_ticks()

        if opcion_elegida.es_correcta:
            self.audio.reproducir_sonido("campana")
            opcion_elegida.estado = "CORRECTO"
            self.estado_respuesta = "ACIERTO"
        else:
            self.audio.reproducir_sonido("click_menu_bw") 
            opcion_elegida.estado = "INCORRECTO"
            self.vidas -= 1
            if self.callback_restar_vida:
                self.callback_restar_vida()
            self.estado_respuesta = "FALLO"

    def update(self, tiempo_pasado):
        #se todavía no se respondeu, podemos responder co rato
        if not self.respondido:
            raton_pos = pygame.mouse.get_pos()
            for opcion in self.opciones:
                opcion.update(raton_pos)

        #se xa se respondeu, esperamos 1 segundo e sacamos da pila a escena para volver ao xogo
        if self.respondido and pygame.time.get_ticks() - self.tiempo_salida > 1000:

            if self.estado_respuesta == "ACIERTO":
                self.indice_pregunta += 1
                
                #se hai pregutas todavía, lanzamos a seguinte 
                if self.indice_pregunta < len(self.banco_preguntas):
                    self.cargar_pregunta_actual()
                    self.respondido = False 
                #se acertou a última pregunta, saímos da escena e avisamos ao xogo que superou a pizarra para que continúe coa historia
                else:
                    self.director.salirEscena()
                    if self.callback_acierto:
                        self.audio.reproducir_sonido("coger_item", self.audio.canal_accion)
                        self.callback_acierto()
            
            elif self.estado_respuesta == "FALLO":
                #se sen vidas, game over
                if self.vidas <= 0:
                    self.director.salirEscena()
                    if self.callback_gameover:
                        self.callback_gameover()
                #se fallou pero aínda ten vidas, volvemos a empezar a mesma pregunta
                else:
                    self.indice_pregunta = 0 #voltamos á primeira pregunta
                    self.cargar_pregunta_actual()
                    self.respondido = False
                    self.director.salirEscena() #sacamos a escena para ter que volver a interactuar

                    #lanzamos o diálogo agora que a pizarra xa se fechou
                    if self.callback_penalizacion:
                        self.callback_penalizacion(self.vidas)

    def dibujar(self, pantalla):
        #sistema anti bucles
        if self in self.director.pila:
            #se seguimos na pila, debuxamos o que ha xusto debaixo
            indice_actual = self.director.pila.index(self)
            if indice_actual > 0:
                escena_anterior = self.director.pila[indice_actual - 1]
                escena_anterior.dibujar(pantalla)
        elif len(self.director.pila) > 0:
            #se xa o sacaron da pila no update(), debuxamos a cima actual, o xogo
            self.director.pila[-1].dibujar(pantalla)    

        #filtro oscuro semitransparente
        overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        pantalla.blit(overlay, (0, 0))

        #debuxar a pizarra
        pygame.draw.rect(pantalla, COLOR_MARCO, self.pizarra_rect.inflate(20, 20), border_radius=10)
        pygame.draw.rect(pantalla, COLOR_PIZARRA, self.pizarra_rect)

        #debuxar o título en varias liñas
        y_offset_titulo = self.pizarra_rect.y + 20
        for linea in self.lineas_pregunta:
            #debuxar a pregunta centrada na parte superior da pizarra
            titulo_render = self.fuente_titulo.render(linea, True, COLOR_TIZA)
            titulo_x = self.pizarra_rect.centerx - (titulo_render.get_width() // 2)
            pantalla.blit(titulo_render, (titulo_x, y_offset_titulo))

            y_offset_titulo += 25


        #delegar o debuxado das opcións a cada unha delas (patrón Componente)
        for opcion in self.opciones:
            opcion.dibujar(pantalla)

        # debuxar as vidas arriba á dereita
        texto_vidas = self.fuente_titulo.render(f"VIDAS: {self.vidas}", True, (255, 100, 100))
        #poñemos as vidas a 30 píxeles do borde dereito e 30 dende arriba
        x_vidas = ANCHO - texto_vidas.get_width() - 30
        y_vidas = 30
        pantalla.blit(texto_vidas, (x_vidas, y_vidas))