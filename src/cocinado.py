import pygame
from gestorAudio import GestorAudio

FONTES = {}

def _fonte(size, bold=False):
    clave = (size, bold)
    if clave not in FONTES:
        FONTES[clave] = pygame.font.SysFont("Calibri", size, bold=bold)
    return FONTES[clave]


# estados dos ingredientes
PATACA_ENTEIRA = "pataca_enteira"
PATACA_CORTADA = "pataca_cortada"
PATACA_FRITA = "pataca_frita"

OVO_ENTEIRO = "ovo_enteiro"
OVO_BATIDO = "ovo_batido"

MESTURA_TORTILLA = "mestura_tortilla"
TORTILLA = "tortilla"

# cores para debug sen usar os sprites
COR_ESTACION = (180, 140, 80)
COR_RESALTADA = (255, 215, 0)
COR_XOGADOR_HUD = (255, 255, 255)

NOMES_INGREDIENTE = {
    PATACA_ENTEIRA: "Pataca",
    PATACA_CORTADA: "Pataca cortada",
    PATACA_FRITA: "Pataca frita",
    OVO_ENTEIRO: "Ovo",
    OVO_BATIDO: "Ovo batido",
    MESTURA_TORTILLA: "Mestura",
    TORTILLA: "Tortilla",
    None: "—",
}


# pataca ou ovo
class Ingrediente:
    def __init__(self, estado):
        self.estado = estado

    def repr(self):
        return f"Ingrediente({self.estado})"

    def nome(self):
        return NOMES_INGREDIENTE.get(self.estado, self.estado)


# as estacións son onde o xogador pode interactuar
# tipo nevera, a táboa de cortar, o fogón, etc.
class Estacion:
    RADIO_INTERACCION = 120

    def __init__(self, nome, rect_mapa):
        self.nome = nome
        self.rect = pygame.Rect(rect_mapa)
        self.ingrediente_na_estacion = None

    def distancia_a(self, xogador):
        cx, cy = self.rect.center
        px, py = xogador.hitbox.center
        return ((cx - px)**2 + (cy - py)**2) ** 0.5

    def xogador_cerca(self, xogador):
        return self.distancia_a(xogador) <= self.RADIO_INTERACCION

    def pode_recibir(self, ingrediente):
        return False

    def pode_dar(self):
        return self.ingrediente_na_estacion is not None

    def accion_x(self, xogador):
        pass

    def update(self, tempo_ms):
        pass

    def dibujar(self, pantalla, camara, resaltada=False):
        rect_cam = camara.aplicar_rect(self.rect)
        cor = COR_RESALTADA if resaltada else COR_ESTACION
        pygame.draw.rect(pantalla, cor, rect_cam, border_radius=6)

        fonte = _fonte(14)
        etiqueta = fonte.render(self.nome, True, (255, 255, 255))
        pantalla.blit(etiqueta, (rect_cam.x + 4, rect_cam.y + 4))

        if self.ingrediente_na_estacion:
            ing_txt = fonte.render(self.ingrediente_na_estacion.nome(), True, (255, 255, 100))
            pantalla.blit(ing_txt, (rect_cam.x + 4, rect_cam.y + 22))


# de onde collemos os alimentos, a neveira e a caixa de patacas
class FonteIngrediente(Estacion):
    """Estación que provee infinitamente un tipo de ingrediente."""
    def __init__(self, nome, rect_mapa, tipo_ingrediente):
        super().__init__(nome, rect_mapa)
        self.tipo = tipo_ingrediente

    def pode_dar(self):
        return True

    def dar_ingrediente(self):
        return Ingrediente(self.tipo)

    def pode_recibir(self, ingrediente):
        return False


class Neveira(FonteIngrediente):
    def __init__(self, rect_mapa):
        super().__init__("Neveira", rect_mapa, OVO_ENTEIRO)


class CaixaPatacas(FonteIngrediente):
    def __init__(self, rect_mapa):
        super().__init__("Caixa Patacas", rect_mapa, PATACA_ENTEIRA)


class TaboaCortar(Estacion):
    PULSACIONS_NECESARIAS = 20

    def __init__(self, rect_mapa):
        super().__init__("Táboa Cortar", rect_mapa)
        self.audio = GestorAudio()
        self.progreso = 0

    def pode_recibir(self, ingrediente):
        return ingrediente.estado == PATACA_ENTEIRA and self.ingrediente_na_estacion is None

    def accion_x(self, xogador):
        if (self.ingrediente_na_estacion and
                self.ingrediente_na_estacion.estado == PATACA_ENTEIRA):
            self.progreso += 1
            self.audio.reproducir_sonido("cortar", self.audio.canal_accion)
            if self.progreso >= self.PULSACIONS_NECESARIAS:
                self.ingrediente_na_estacion.estado = PATACA_CORTADA
                self.progreso = 0

    def dibujar(self, pantalla, camara, resaltada=False):
        super().dibujar(pantalla, camara, resaltada)
        if (self.ingrediente_na_estacion and
                self.ingrediente_na_estacion.estado == PATACA_ENTEIRA):
            rect_cam = camara.aplicar_rect(self.rect)
            barra_ancho = int(self.rect.width * (self.progreso / self.PULSACIONS_NECESARIAS))
            barra_rect = pygame.Rect(rect_cam.x, rect_cam.bottom - 8, barra_ancho, 8)
            pygame.draw.rect(pantalla, (100, 200, 100), barra_rect)

class Fogon(Estacion):
    TEMPO_COCCION_MS = 10_000

    ACEPTA = {
        PATACA_CORTADA: PATACA_FRITA,
        MESTURA_TORTILLA: TORTILLA,
    }

    def __init__(self, rect_mapa):
        super().__init__("Fogón", rect_mapa)
        self.audio = GestorAudio()
        self.canal_hervir = None # Para poder reproducir o fogón en bucle
        self.tempo_acumulado = 0
        self.cocinando = False

    def pode_recibir(self, ingrediente):
        return (ingrediente.estado in self.ACEPTA and
                self.ingrediente_na_estacion is None)

    def depositar(self, ingrediente):
        self.ingrediente_na_estacion = ingrediente
        self.tempo_acumulado = 0
        self.cocinando = True

        # O mixer usa un canal libre para o son de fervir.
        # Este se usa en "reproducir_sonido" (así podese parar o son máis tarde):
        self.canal_hervir = pygame.mixer.find_channel(True)
        self.audio.reproducir_sonido("hervir", self.canal_hervir, loops = -1)

    def update(self, tempo_ms):
        if self.cocinando and self.ingrediente_na_estacion:
            estado = self.ingrediente_na_estacion.estado
            if estado in self.ACEPTA:
                self.tempo_acumulado += tempo_ms
                if self.tempo_acumulado >= self.TEMPO_COCCION_MS:
                    self.ingrediente_na_estacion.estado = self.ACEPTA[estado]
                    self.cocinando = False
                    if self.canal_hervir:
                        self.canal_hervir.fadeout(200)
                        self.canal_hervir = None
            else:
                self.cocinando = False

    def pode_dar(self):
        if self.ingrediente_na_estacion is None:
            return False
        return self.ingrediente_na_estacion.estado in (PATACA_FRITA, TORTILLA)

    def dibujar(self, pantalla, camara, resaltada=False):
        super().dibujar(pantalla, camara, resaltada)
        if self.cocinando and self.ingrediente_na_estacion:
            rect_cam = camara.aplicar_rect(self.rect)
            progreso = min(self.tempo_acumulado / self.TEMPO_COCCION_MS, 1.0)
            barra_ancho = int(self.rect.width * progreso)
            barra_rect = pygame.Rect(rect_cam.x, rect_cam.bottom - 8, barra_ancho, 8)
            pygame.draw.rect(pantalla, (255, 165, 0), barra_rect)

class Cunca(Estacion):
    PULSACIONS_BATER = 30

    def __init__(self, rect_mapa):
        super().__init__("Cunca", rect_mapa)
        self.audio = GestorAudio()
        self.ovo = None
        self.pataca_frita = None
        self.progreso_bater = 0
        self.mestura_lista = False

    def pode_recibir(self, ingrediente):
        if self.mestura_lista:
            return False
        if ingrediente.estado == OVO_ENTEIRO and self.ovo is None:
            return True
        if ingrediente.estado == PATACA_FRITA and self.pataca_frita is None:
            return True
        return False

    def recibir(self, ingrediente):
        if ingrediente.estado == OVO_ENTEIRO:
            self.ovo = ingrediente
        elif ingrediente.estado == PATACA_FRITA:
            self.pataca_frita = ingrediente
        self.comprobar_mestura()

    def comprobar_mestura(self):
        if (self.ovo and self.ovo.estado == OVO_BATIDO and self.pataca_frita):
            self.mestura_lista = True
            self.ingrediente_na_estacion = Ingrediente(MESTURA_TORTILLA)
            self.ovo = None
            self.pataca_frita = None

    def pode_dar(self):
        return self.mestura_lista

    def accion_x(self, xogador):
        if self.ovo and self.ovo.estado == OVO_ENTEIRO:
            self.progreso_bater += 1
            self.audio.reproducir_sonido("batir", self.audio.canal_accion)
            if self.progreso_bater >= self.PULSACIONS_BATER:
                self.ovo.estado = OVO_BATIDO
                self.progreso_bater = 0
                self.comprobar_mestura()

    def dibujar(self, pantalla, camara, resaltada=False):
        super().dibujar(pantalla, camara, resaltada)
        rect_cam = camara.aplicar_rect(self.rect)

        linhas = []
        if self.ovo:
            linhas.append(f"Ovo: {self.ovo.nome()}")
        if self.pataca_frita:
            linhas.append("Pataca frita")
        if self.mestura_lista:
            linhas.append("Mestura lista!")

        fonte = _fonte(13)
        for i, txt in enumerate(linhas):
            surf = fonte.render(txt, True, (200, 255, 200))
            pantalla.blit(surf, (rect_cam.x + 4, rect_cam.y + 38 + i * 14))

        if self.ovo and self.ovo.estado == OVO_ENTEIRO:
            progreso = self.progreso_bater / self.PULSACIONS_BATER
            barra_ancho = int(self.rect.width * progreso)
            barra_rect = pygame.Rect(rect_cam.x, rect_cam.bottom - 8, barra_ancho, 8)
            pygame.draw.rect(pantalla, (255, 220, 50), barra_rect)

class Prato(Estacion):
    def __init__(self, rect_mapa):
        super().__init__("Prato", rect_mapa)

    def pode_recibir(self, ingrediente):
        return (ingrediente.estado in (PATACA_FRITA, TORTILLA) and
                self.ingrediente_na_estacion is None)

class Mostrador(Estacion):
    def __init__(self, rect_mapa, callback_punto=None):
        super().__init__("Mostrador", rect_mapa)
        self.callback_punto = callback_punto

    def pode_recibir(self, ingrediente):
        return ingrediente.estado == TORTILLA

    def recibir_entrega(self, ingrediente):
        if self.callback_punto:
            self.callback_punto()

    def dibujar(self, pantalla, camara, resaltada=False):
        rect_cam = camara.aplicar_rect(self.rect)
        cor = (255, 215, 0) if resaltada else (200, 160, 50)
        pygame.draw.rect(pantalla, cor, rect_cam, border_radius=6)
        fonte = _fonte(14, bold=True)
        lbl = fonte.render("ENTREGAR", True, (0, 0, 0))
        pantalla.blit(lbl, lbl.get_rect(center=rect_cam.center))

class XestorCocina:
    def __init__(self, xogador, posicions=None):
        self.audio = GestorAudio()
        self.xogador = xogador
        self.man = None  

        pos = posicions or {
            "neveira": pygame.Rect(16, 2600, 100, 100), 
            "caixa_patacas": pygame.Rect(700, 3100, 70, 70), 
            "taboa": pygame.Rect(570, 3100, 70, 70), 
            "Fogon": pygame.Rect(450, 2640, 70, 70), 
            "cunca": pygame.Rect(390, 3100, 70, 70), 
            "prato": pygame.Rect(320, 2640, 70, 70), 
            "mostrador": pygame.Rect(32, 3130, 110, 90), 
        }

        self.neveira = Neveira(pos["neveira"])
        self.caixa_patacas = CaixaPatacas(pos["caixa_patacas"])
        self.taboa = TaboaCortar(pos["taboa"])
        self.Fogon = Fogon(pos["Fogon"])
        self.cunca = Cunca(pos["cunca"])
        self.prato = Prato(pos["prato"])
        self.mostrador = Mostrador(pos["mostrador"], self.sumar_punto)

        self.estacions = [
            self.neveira, self.caixa_patacas,
            self.taboa, self.Fogon,
            self.cunca, self.prato, self.mostrador,
        ]

        self.puntos = 0
        self._estacion_preto = None

    def sumar_punto(self):
        self.puntos += 1
        print(f"[Cocina] Tortilla entregada! Puntos: {self.puntos}")

    def get_estacion_preto(self):
        preto = None
        menor = float("inf")
        for est in self.estacions:
            if est.xogador_cerca(self.xogador):
                d = est.distancia_a(self.xogador)
                if d < menor:
                    menor = d
                    preto = est
        return preto

    def accion_e(self):
        est = self._estacion_preto
        if est is None:
            return

        # Mostrador onde entregamos
        if isinstance(est, Mostrador):
            if self.man and self.man.estado == TORTILLA:
                self.audio.reproducir_sonido("campana", self.audio.canal_accion)
                est.recibir_entrega(self.man)
                self.man = None
            return

        # man chea -> intentar depositar
        if self.man is not None:
            if isinstance(est, Cunca) and est.pode_recibir(self.man):
                self.audio.reproducir_sonido("dejar_item", self.audio.canal_accion) # Son ao deixar un ítem
                est.recibir(self.man)
                self.man = None
                return
            if isinstance(est, Fogon) and est.pode_recibir(self.man):
                self.audio.reproducir_sonido("dejar_item", self.audio.canal_accion)
                est.depositar(self.man)
                self.man = None
                return
            if est.pode_recibir(self.man):
                est.ingrediente_na_estacion = self.man
                self.audio.reproducir_sonido("dejar_item", self.audio.canal_accion)
                self.man = None
            return

        # man baleira -> intentar coller
        if est.pode_dar():
            if isinstance(est, FonteIngrediente):
                self.audio.reproducir_sonido("coger_item", self.audio.canal_accion) # Son ao coller un ítem
                self.man = est.dar_ingrediente()
            else:
                self.man = est.ingrediente_na_estacion
                est.ingrediente_na_estacion = None
                if isinstance(est, Cunca):
                    est.mestura_lista = False
                self.audio.reproducir_sonido("coger_item", self.audio.canal_accion)

    def accion_x(self):
        if self._estacion_preto is not None:
            self._estacion_preto.accion_x(self.xogador)

    def eventos(self, lista_eventos):
        for evento in lista_eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_e:
                    self.accion_e()
                elif evento.key == pygame.K_x:
                    self.accion_x()

    def update(self, tempo_ms):
        self._estacion_preto = self.get_estacion_preto()
        for est in self.estacions:
            est.update(tempo_ms)

    def dibujar(self, pantalla, camara):
        for est in self.estacions:
            est.dibujar(pantalla, camara, resaltada=(est is self._estacion_preto))
        self.dibujar_hud(pantalla)

    def dibujar_hud(self, pantalla):
        fonte = _fonte(20, bold=True)

        txt_puntos = fonte.render(f"Tortillas: {self.puntos}", True, (255, 215, 0))
        pantalla.blit(txt_puntos, (10, 10))

        nome_man = self.man.nome() if self.man else "Baleira"
        txt_man  = fonte.render(f"Man: {nome_man}", True, COR_XOGADOR_HUD)
        pantalla.blit(txt_man, (10, 35))

        if self._estacion_preto:
            txt_est = fonte.render(
                f"[E] {self._estacion_preto.nome}  [X] Accion",
                True, (200, 255, 200)
            )
            pantalla.blit(txt_est, (10, 60))