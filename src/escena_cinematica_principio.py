import pygame
import os
from escena import Escena, ANCHO, ALTO
from gestorAudio import GestorAudio
from escena_dialogo import EscenaDialogo

class EscenaCinematicaPrincipio(Escena):
    def __init__(self, director):
        super().__init__(director)
        self.audio = GestorAudio()
        
        # rutas q hacen falta pa las fotos
        self.HOME = os.path.dirname(__file__)
        self.ASSETS = os.path.join(self.HOME, "..", "assets")
        self.GRAPHICS = os.path.join(self.ASSETS, "graphics")
        
        # cosas q salen en pantalla
        self.bg_img = None
        self.char_img = None
        self.item_img = None
        
        # flags pa los ifs y animaciones de fundido 
        self.fase = 0
        self.estado = "FADE_IN" # control de estados basicos
        self.fade_alpha = 255
        self.timer = 0
        self.espera_max = 0
        
        # variables para la animación del ítem
        self.item_y = ALTO
        self.item_y_final = ALTO
        
        # textos
        self.dialogues1 = [
            "Era principios de Septiembre de 20XX...",
            "En un lugar de la UDC, de cuyo nombre no quiero acordarme...",
            "Donde los autobuses siempre van o vacíos o llevan a facultades enteras dentro..."
        ]
        self.dialogues2 = [
            "Carlitos, (por alguna razón) estaba muy emocionado de empezar su primer año...",
            "Sin embargo...",
            "No tenía ni idea de lo que su destino le depararía..."
        ]
        self.dialogues3 = ["Hola pichi, ¿qué vas a querer?", "¿Una tortilla? Maaaaarchando papi."]
        self.dialogues3_jumpscare = ["¡LÁZARO UNA TORTILLA PARA EL RUBIO ESTE!"]
        self.dialogues3_tras = ["(Carlitos no es rubio)"]
        self.dialogues4_tortilla = ["Aquí tienes tu tortilla, papi.", "Que aproveche.", "Espera pichi, primero tienes que pagar.", "Serían $$$ en total."]
        self.dialogues4_enfadado = ["¿Cómo que no tienes dinero?", "¡¿?!"]
        self.dialogues4_golpe = ["(Carlitos siente un duro golpe y la vista se le pone en negro)"]
        self.dialogue_transicion = ["Parece que Michel ha secuestrado a Carlitos...", "Y lo va a obligar a trabajar en la cafetería para pagar su deuda."]
        
        # iniciar la cinemática
        self.cargar_fondo(os.path.join(self.GRAPHICS, "cinematica", "bus1.png"))
        self.audio.reproducir_musica("parada_bus", -1, 1000)
        self.ejecutar_fase()

    def cargar_fondo(self, ruta):
        if ruta == "NEGRO":
            self.bg_img = pygame.Surface((ANCHO, ALTO))
            self.bg_img.fill((0, 0, 0))
        else:
            img = pygame.image.load(ruta).convert()
            self.bg_img = pygame.transform.scale(img, (ANCHO, ALTO))
            
    def cargar_personaje(self, ruta, scale=4):
        if ruta is None:
            self.char_img = None
            return
        img = pygame.image.load(ruta).convert_alpha()
        self.char_img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))

    def cargar_item(self, ruta, scale=1):
        if ruta is None:
            self.item_img = None
            return
        img = pygame.image.load(ruta).convert_alpha()
        self.item_img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))

    def avanzar(self):
        self.fase += 1
        self.ejecutar_fase()

    def lanzar_dialogo(self, textos, voz="voz_narrador"):
        self.estado = "PAUSADO"
        self.director.apilarEscena(EscenaDialogo(self.director, textos, voz, callback_fin=self.avanzar))

    def ejecutar_fase(self):
        # máquina de estados que define la progresión lógica de la cinemática.
        if self.fase == 0:
            self.estado = "FADE_IN"
        elif self.fase == 1:
            self.lanzar_dialogo(self.dialogues1)
        elif self.fase == 2:
            self.estado = "FADE_OUT"
        elif self.fase == 3:
            self.cargar_fondo(os.path.join(self.GRAPHICS, "cinematica", "facu1.png"))
            self.estado = "FADE_IN"
        elif self.fase == 4:
            self.lanzar_dialogo(self.dialogues2)
        elif self.fase == 5:
            self.audio.detener_musica(500)
            self.estado = "FADE_OUT"
        elif self.fase == 6:
            self.cargar_fondo(os.path.join(self.GRAPHICS, "cinematica", "cafeta.png"))
            self.cargar_personaje(os.path.join(self.GRAPHICS, "characters", "míchel", "michel_normal.png"), 0.60)
            self.audio.reproducir_musica("cafeteria", -1, 1000)
            self.estado = "FADE_IN"
        elif self.fase == 7:
            self.audio.reproducir_sonido("m_buenos_dias_pichi")
            self.lanzar_dialogo(self.dialogues3, "voz_michel")
        elif self.fase == 8:
            self.cargar_personaje(os.path.join(self.GRAPHICS, "characters", "míchel", "michel_jumpScare.png"), 0.75)
            self.lanzar_dialogo(self.dialogues3_jumpscare, "voz_michel")
        elif self.fase == 9:
            self.audio.reproducir_sonido("m_risa_malevola")
            self.lanzar_dialogo(self.dialogues3_tras)
        elif self.fase == 10:
            self.cargar_personaje(None)
            self.estado = "FADE_OUT"
        elif self.fase == 11:
            self.cargar_personaje(os.path.join(self.GRAPHICS, "characters", "míchel", "michel_normal.png"), 0.60)
            self.cargar_item(os.path.join(self.GRAPHICS, "ui", "tortilla.png"), 0.5)
            self.estado = "FADE_IN"
        elif self.fase == 12:
            self.audio.reproducir_sonido("m_una_tortillita")
            self.lanzar_dialogo(self.dialogues4_tortilla, "voz_michel")
        elif self.fase == 13:
            self.cargar_personaje(None)
            self.cargar_item(os.path.join(self.GRAPHICS, "ui", "cartera_vacia.png"), 0.8)
            self.item_y = ALTO
            self.item_y_final = ALTO - self.item_img.get_height()
            
            self.estado = "SUBIR_ITEM"
        elif self.fase == 14:
            self.estado = "ESPERA"
            self.espera_max = 2500
            self.timer = 0
        elif self.fase == 15:
            self.cargar_item(None) 
            self.cargar_personaje(os.path.join(self.GRAPHICS, "characters", "míchel", "michel_enfadao.png"), 0.60)
            self.lanzar_dialogo(self.dialogues4_enfadado, "voz_michel_grave")
        elif self.fase == 16:
            self.lanzar_dialogo(self.dialogues4_golpe)
        elif self.fase == 17:
            self.cargar_personaje(None)
            self.audio.reproducir_sonido("m_buenas_noches")
            self.estado = "ESPERA"
            self.espera_max = 1000
            self.timer = 0
        elif self.fase == 18:
            self.audio.reproducir_sonido("golpe_sarten")
            self.estado = "ESPERA"
            self.espera_max = 500
            self.timer = 0
        elif self.fase == 19:
            self.audio.detener_musica(500)
            self.estado = "FADE_OUT"
        elif self.fase == 20:
            self.cargar_fondo("NEGRO")
            self.estado = "ESPERA"
            self.espera_max = 1000
            self.timer = 0
        elif self.fase == 21:
            self.lanzar_dialogo(self.dialogue_transicion)
        elif self.fase == 22:
            self.saltar_cinematica() 

    def saltar_cinematica(self):
        self.audio.detener_musica(100)
        self.audio.canal_texto.stop()
        from game import Juego
        self.director.cambiarEscena(Juego(self.director))

    def eventos(self, lista_eventos):
        for evento in lista_eventos:
            if evento.type == pygame.QUIT:
                self.director.salirPrograma()
                
            # en la cinemática bloqueamos otras teclas pa no liar al director
            # DEBUG para skipear cinemática entera (desactivado)
            # if evento.type == pygame.KEYDOWN and evento.key == pygame.K_q:
            #    self.saltar_cinematica()

    def update(self, tiempo_pasado):
        if self.estado == "FADE_IN":
            self.fade_alpha -= (255 / 1000) * tiempo_pasado # fade de 1 segundo
            if self.fade_alpha <= 0:
                self.fade_alpha = 0
                self.avanzar()
                
        elif self.estado == "FADE_OUT":
            self.fade_alpha += (255 / 1000) * tiempo_pasado
            if self.fade_alpha >= 255:
                self.fade_alpha = 255
                self.avanzar()
                
        elif self.estado == "ESPERA":
            self.timer += tiempo_pasado
            if self.timer >= self.espera_max:
                self.avanzar()
                
        elif self.estado == "SUBIR_ITEM":
            velocidad_subida = 0.5 # Píxeles por ms
            self.item_y -= velocidad_subida * tiempo_pasado
            if self.item_y <= self.item_y_final:
                self.item_y = self.item_y_final
                self.avanzar()

    def dibujar(self, pantalla):
        # 1. el fondo
        if self.bg_img:
            pantalla.blit(self.bg_img, (0, 0))
            
        # caja de texto q mide 150 
        textbox_top_y = ALTO - 150
        
        # 2. pinta el personaje
        if self.char_img:
            # para hacer que michel quede alineado con el textbox
            hundimiento_personaje = 30 
            
            char_x = (ANCHO - self.char_img.get_width()) // 2
            char_y = textbox_top_y - self.char_img.get_height() + hundimiento_personaje
            
             # para la parte de michel y tortilla
            if self.item_img:
                char_x = (ANCHO // 2) - self.char_img.get_width() + 40
                
            pantalla.blit(self.char_img, (char_x, char_y))
            
        # 3. dibujar a michel si la hay
        if self.item_img:
            if self.char_img is None:
                item_x = (ANCHO - self.item_img.get_width()) // 2
                item_y_draw = self.item_y
            else:
                item_x = (ANCHO // 2) - 40
                item_y_draw = textbox_top_y - self.item_img.get_height()
                
            pantalla.blit(self.item_img, (item_x, item_y_draw))
            
        # 4. dibujar la cortina negra de los fades
        if self.fade_alpha > 0:
            s = pygame.Surface((ANCHO, ALTO))
            s.fill((0, 0, 0))
            s.set_alpha(int(self.fade_alpha))
            pantalla.blit(s, (0, 0))