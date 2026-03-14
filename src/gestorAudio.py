import pygame
import os

HOME = os.path.dirname(__file__)
ASSESTS_FILE = os.path.join(HOME, "..", "assets")
SOUNDS_FILE = os.path.join(ASSESTS_FILE, "sounds")
SFX_FILE = os.path.join(SOUNDS_FILE, "sfx")
MUSIC_FILE = os.path.join(SOUNDS_FILE, "music")

#volumen base
VOL_SFX = 1.0
VOL_MUSICA = 0.6

#clase para controlar el audio de todo el juego
class GestorAudio:
    _instance = None #instancia única

    #patrón singleton para no crear mil gestores de audio
    def __new__(cls):
        if cls._instance is None:

            #iniciamos el mixer si no estaba ya
            if not pygame.mixer.get_init():
                pygame.mixer.pre_init(44100, 16, 2, 4096)
                pygame.mixer.init()
            
            cls._instance = super().__new__(cls)
            cls._instance._inicializado = False
        return cls._instance

    def __init__(self):
        #si ya se inició pasamos de volver a hacerlo
        if getattr(self, "_inicializado", False):
            return
        self._inicializado = True
        
        #ajustamos volumen
        self.volumen_sfx = VOL_SFX
        self.volumen_musica = VOL_MUSICA

        self.sonidos = {} #diccionario para guardar los sfx
        self.musica = {} #y este para la música
        self.musica_actual = None #canción sonando ahora

        #cargamos todos los sonidos:
        self.cargar_sonido("click_menu_fw", os.path.join(SFX_FILE, "click_menu_fw.wav")) #interfaz
        self.cargar_sonido("click_menu_bw", os.path.join(SFX_FILE, "click_menu_bw.wav"))
        self.cargar_sonido("click_menu_big", os.path.join(SFX_FILE, "click_menu_big.wav"))
        self.cargar_sonido("burbuja_texto", os.path.join(SFX_FILE, "burbuja_texto.wav"))
        self.cargar_sonido("pasos", os.path.join(SFX_FILE, "footsteps.wav")) #movimiento
        self.cargar_sonido("coger_item", os.path.join(SFX_FILE, "coger_item.wav")) #interacciones
        self.cargar_sonido("dejar_item", os.path.join(SFX_FILE, "dejar_item.wav"))
        self.cargar_sonido("cortar", os.path.join(SFX_FILE, "cortar.wav")) #cocina
        self.cargar_sonido("batir", os.path.join(SFX_FILE, "batir.wav"))
        self.cargar_sonido("hervir", os.path.join(SFX_FILE, "boiling.wav"))
        self.cargar_sonido("campana", os.path.join(SFX_FILE, "campana.wav"))
        self.cargar_sonido("voz_narrador", os.path.join(SFX_FILE, "blip_narrador.wav")) #blips de voces
        self.cargar_sonido("voz_michel", os.path.join(SFX_FILE, "blip_michel.wav"))
        self.cargar_sonido("voz_michel_grave", os.path.join(SFX_FILE, "blip_michel_grave.wav"))
        self.cargar_sonido("voz_carlitos", os.path.join(SFX_FILE, "blip_carlitos.wav"))
        self.cargar_sonido("golpe_sarten", os.path.join(SFX_FILE, "golpe_sarten.wav")) #cutscene
        self.cargar_sonido("m_buenos_dias_papi", os.path.join(SFX_FILE, "michel_buenos_dias_papi.wav")) #frases de michel
        self.cargar_sonido("m_buenos_dias_pichi", os.path.join(SFX_FILE, "michel_buenos_dias_pichi.wav"))
        self.cargar_sonido("m_buenas_noches", os.path.join(SFX_FILE, "michel_buenas_noches.wav"))
        self.cargar_sonido("m_una_tortillita", os.path.join(SFX_FILE, "michel_una_tortillita.wav"))
        self.cargar_sonido("m_risa_malevola", os.path.join(SFX_FILE, "michel_risa_malevola.wav"))
        self.cargar_sonido("m_amenaza", os.path.join(SFX_FILE, "michel_te_amenaza.wav"))
        self.cargar_sonido("m_risa_malevola_final", os.path.join(SFX_FILE, "michel_risa_malevola_slowdown&reverb.wav")) #una risa loca que metimos
        self.cargar_sonido("pasos_pasillo", os.path.join(SFX_FILE, "pasos_caseros.wav"))
        self.cargar_sonido("toc_toc", os.path.join(SFX_FILE, "629987__flem0527__knocking-on-wood-door-1.wav"))
        self.cargar_sonido("abre_puerta", os.path.join(SFX_FILE, "15419__pagancow__dorm-door-opening.wav"))



        #la música solo guardamos la ruta, no la cargamos entera en memoria:
        self.musica["cocina"] = os.path.join(MUSIC_FILE, "Cocina.mp3")
        self.musica["escape"] = os.path.join(MUSIC_FILE, "Escape.mp3")
        self.musica["cafeteria"] = os.path.join(MUSIC_FILE, "ambiente_cafeteria.mp3")
        self.musica["parada_bus"] = os.path.join(MUSIC_FILE, "ambiente_parada_bus.mp3")
        self.musica["una_vida_restante"] = os.path.join(MUSIC_FILE, "175205__minigunfiend__scary-creaking-knocking-wood.wav")
        self.musica["dos_vidas_restantes"] = os.path.join(MUSIC_FILE, "Scary-Monster.flac")
        self.musica["jumpscare_musica"] = os.path.join(MUSIC_FILE, "Scary Ambient Wind.ogg")

        #reservamos canales para cosas específicas
        pygame.mixer.set_reserved(4)
        self.canal_ui = pygame.mixer.Channel(0) #interfaz
        self.canal_personaje = pygame.mixer.Channel(1) #prota (como los pasos)
        self.canal_accion = pygame.mixer.Channel(2) #acciones (coger ítems...)
        self.canal_texto = pygame.mixer.Channel(3) #textos y diálogos
    
    #cargamos el sonido y lo guardamos
    def cargar_sonido(self, nombre, ruta):
        sonido = pygame.mixer.Sound(ruta)
        sonido.set_volume(self.volumen_sfx)
        self.sonidos[nombre] = sonido #lo metemos al dict

    #darle al play a un sonido
    def reproducir_sonido(self, nombre, canal = None, loops = 0, fadein = 0):
        if nombre in self.sonidos:
            if canal is not None: #si pasamos un canal concreto
                canal.play(self.sonidos[nombre], loops, fade_ms = fadein)
            else:
                self.sonidos[nombre].play(loops, fade_ms = fadein)
    
    #darle al play a la música
    def reproducir_musica(self, nombre, loops = -1, fadein = 0):
        if nombre in self.musica:
            musica = self.musica[nombre]
            pygame.mixer.music.load(musica)
            pygame.mixer.music.set_volume(self.volumen_musica)

            #la ponemos en bucle sin fade-in a menos que le digamos otra cosa
            pygame.mixer.music.play(loops, fade_ms = fadein)
            self.musica_actual = nombre
    
    #pausar la música dejando donde estaba
    def pausar_musica(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
    
    #quitar la pausa
    def reanudar_musica(self):
        pygame.mixer.music.unpause()
    
    #parar del todo la música
    def detener_musica(self, fadeout = 1000):
        if pygame.mixer.music.get_busy():

            #paramos con un fade-out suave por defecto
            pygame.mixer.music.fadeout(fadeout)
            self.musica_actual = None
    
    #cambiar volumen 
    def cambiar_volumen_musica(self, volumen):
        volumen = max(0.0, min(1.0, volumen)) #ni más de 1 ni menos de 0
        self.volumen_musica = volumen
        pygame.mixer.music.set_volume(self.volumen_musica)