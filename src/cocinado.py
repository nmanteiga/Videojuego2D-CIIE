import os
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
BOL_OVO = "bol_ovo"
BOL_PATACA = "bol_pataca"

MESTURA_TORTILLA = "mestura_tortilla"
TORTILLA = "tortilla"

COR_XOGADOR_HUD = (255, 255, 255)

NOMES_INGREDIENTE = {
    PATACA_ENTEIRA: "Patacas",
    PATACA_CORTADA: "Patacas cortadas",
    PATACA_FRITA: "Patacas fritas",
    OVO_ENTEIRO: "Ovos",
    OVO_BATIDO: "Ovos batidos",
    MESTURA_TORTILLA: "Mestura",
    TORTILLA: "Tortilla",
    None: "—",
}

_HIGHLIGHT_SCALE = 4
_HIGHLIGHTS_CACHE = {}

def _cargar_highlight(graphics_dir, nome):
    if nome not in _HIGHLIGHTS_CACHE:
        ruta = os.path.join(graphics_dir, "environments", nome)
        img = pygame.image.load(ruta).convert_alpha()
        w = img.get_width() * _HIGHLIGHT_SCALE
        h = img.get_height() * _HIGHLIGHT_SCALE
        _HIGHLIGHTS_CACHE[nome] = pygame.transform.scale(img, (w, h))
    return _HIGHLIGHTS_CACHE[nome]

def inicializar_highlights(graphics_dir):
    for nome in (
        "highlight_ovos.png",
        "highlight_patacas.png",
        "highlight_cortar.png",
        "highlight_fritir.png",
        "highlight_bol.png",
        "highlight_prato.png",
        "highlight_entrega.png",
    ):
        _cargar_highlight(graphics_dir, nome)

_ITEM_SCALE = 4
_item_archivos = {
    PATACA_ENTEIRA:   "pataca.png",
    PATACA_CORTADA:   "pataca_cortada.png",
    PATACA_FRITA:     "pataca_frita.png",
    OVO_ENTEIRO:      "ovo.png",
    BOL_OVO:       "bol_ovo.png",
    BOL_PATACA:       "bol_pataca.png",
    MESTURA_TORTILLA: "bol_mezcla.png",
    TORTILLA:         "plato_tortilla.png",
}

_sprites_man = {}

_ESTACION_SCALE = 4.5
_estacion_sprites = {}

def _cargar_sprites_estacion(graphics_dir):
    env_dir = os.path.join(graphics_dir, "environments")
    for nome in ("sarten.png", "sarten_cocinando.png", "bol.png", "bol_mezcla.png"):
        ruta = os.path.join(env_dir, nome)
        img = pygame.image.load(ruta).convert_alpha()
        w = img.get_width()  * _ESTACION_SCALE
        h = img.get_height() * _ESTACION_SCALE
        _estacion_sprites[nome] = pygame.transform.scale(img, (w, h))

def _cargar_sprites_man(graphics_dir):
    global _sprites_man
    env_dir = os.path.join(graphics_dir, "environments")
    for estado, fname in _item_archivos.items():
        ruta = os.path.join(env_dir, fname)
        img = pygame.image.load(ruta).convert_alpha()
        w = img.get_width()  * _ITEM_SCALE
        h = img.get_height() * _ITEM_SCALE
        _sprites_man[estado] = pygame.transform.scale(img, (w, h))

class Ingrediente:
    def __init__(self, estado):
        self.estado = estado

    def repr(self):
        return f"Ingrediente({self.estado})"

    def nome(self):
        return NOMES_INGREDIENTE.get(self.estado, self.estado)

class Estacion:
    RADIO_INTERACCION = 80
    COS_ANGULO_MIN = 0.4

    def __init__(self, nome, rect_mapa):
        self.nome = nome
        self.rect = pygame.Rect(rect_mapa)
        self.ingrediente_na_estacion = None

    def distancia_a(self, xogador):
        cx, cy = self.rect.center
        px, py = xogador.hitbox.center
        return ((cx - px)**2 + (cy - py)**2) ** 0.5

    def _dir_xogador(self, xogador):
        base    = xogador.last_action_base
        dx_sign = 1 if xogador.facing_right else -1
        if base == 'up': return (0.0, -1.0)
        if base == 'down': return (0.0,  1.0)
        if base == 'r': return (float(dx_sign), 0.0)
        if base == 'dup': return (dx_sign / 1.4142,  1.0 / 1.4142)
        if base == 'ddown': return (dx_sign / 1.4142, -1.0 / 1.4142)
        return (0.0, 1.0)

    def xogador_cara_a(self, xogador):
        cx, cy = self.rect.center
        px, py = xogador.hitbox.center
        ex, ey = cx - px, cy - py
        dist = (ex**2 + ey**2) ** 0.5
        if dist == 0:
            return True
        ex /= dist; ey /= dist
        dx, dy = self._dir_xogador(xogador)
        return dx * ex + dy * ey >= self.COS_ANGULO_MIN

    def xogador_cerca(self, xogador):
        return (self.distancia_a(xogador) <= self.RADIO_INTERACCION and
                self.xogador_cara_a(xogador))

    def pode_recibir(self, ingrediente): return False
    def pode_dar(self): return self.ingrediente_na_estacion is not None
    def accion_x(self, xogador): pass
    def update(self, tempo_ms): pass

    def dibujar(self, pantalla, camara, highlight_nome=None):
        if highlight_nome and highlight_nome in _HIGHLIGHTS_CACHE:
            surf = _HIGHLIGHTS_CACHE[highlight_nome]
            mapa_rect = pygame.Rect(0, 0, surf.get_width(), surf.get_height())
            pantalla.blit(surf, camara.aplicar_rect(mapa_rect))

class FonteIngrediente(Estacion):
    def __init__(self, nome, rect_mapa, tipo_ingrediente):
        super().__init__(nome, rect_mapa)
        self.tipo = tipo_ingrediente

    def pode_dar(self): return True
    def dar_ingrediente(self): return Ingrediente(self.tipo)
    def pode_recibir(self, i): return False


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

    def dibujar(self, pantalla, camara, highlight_nome=None):
        super().dibujar(pantalla, camara, highlight_nome)
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
        self.canal_hervir = None
        self.tempo_acumulado = 0
        self.cocinando = False

    def pode_recibir(self, ingrediente):
        return (ingrediente.estado in self.ACEPTA and
                self.ingrediente_na_estacion is None)

    def depositar(self, ingrediente):
        self.ingrediente_na_estacion = ingrediente
        self.tempo_acumulado = 0
        self.cocinando = True
        self.canal_hervir = pygame.mixer.find_channel(True)
        self.audio.reproducir_sonido("hervir", self.canal_hervir, loops=-1)

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

    def dibujar(self, pantalla, camara, highlight_nome=None):
        super().dibujar(pantalla, camara, highlight_nome)
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
        if self.mestura_lista: return False
        if ingrediente.estado == OVO_ENTEIRO and self.ovo is None: return True
        if ingrediente.estado == PATACA_FRITA and self.pataca_frita is None: return True
        return False

    def recibir(self, ingrediente):
        if   ingrediente.estado == OVO_ENTEIRO: self.ovo = ingrediente
        elif ingrediente.estado == PATACA_FRITA: self.pataca_frita = ingrediente
        self.comprobar_mestura()

    def comprobar_mestura(self):
        if (self.ovo and self.ovo.estado == OVO_BATIDO and self.pataca_frita):
            self.mestura_lista = True
            self.ingrediente_na_estacion = Ingrediente(MESTURA_TORTILLA)
            self.ovo = None
            self.pataca_frita = None

    def pode_dar(self): return self.mestura_lista

    def accion_x(self, xogador):
        if self.ovo and self.ovo.estado == OVO_ENTEIRO:
            self.progreso_bater += 1
            self.audio.reproducir_sonido("batir", self.audio.canal_accion)
            if self.progreso_bater >= self.PULSACIONS_BATER:
                self.ovo.estado = OVO_BATIDO
                self.progreso_bater = 0
                self.comprobar_mestura()

    def dibujar(self, pantalla, camara, highlight_nome=None):
        super().dibujar(pantalla, camara, highlight_nome)
        if self.ovo and self.ovo.estado == OVO_ENTEIRO:
            rect_cam = camara.aplicar_rect(self.rect)
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


class XestorCocina:
    def __init__(self, xogador, graphics_dir, posicions=None):
        self.audio = GestorAudio()
        self.xogador = xogador
        self.man = None

        inicializar_highlights(graphics_dir)
        _cargar_sprites_man(graphics_dir)
        _cargar_sprites_estacion(graphics_dir)

        pos = posicions or {
            "neveira": pygame.Rect( 16, 2650, 70, 100),
            "caixa_patacas": pygame.Rect(720, 3050, 50,  50),
            "taboa": pygame.Rect(580, 3100, 50,  50),
            "Fogon": pygame.Rect(460, 2640, 50,  40),
            "cunca": pygame.Rect(390, 3100, 50,  50),
            "prato": pygame.Rect(330, 2640, 50,  40),
            "mostrador": pygame.Rect( 65, 3150, 60,  40),
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
        self.primeira_tortilla_feita = False
        self.deuda = 3.00

    def sumar_punto(self):
        self.puntos += 1
        self.primeira_tortilla_feita = True
        self.deuda = max(0.0, self.deuda - 0.02)
        print(f"[Cocina] Tortilla entregada! Puntos: {self.puntos} | Deuda: {self.deuda:.2f}€")

    def get_estacion_preto(self):
        preto, menor = None, float("inf")
        for est in self.estacions:
            if est.xogador_cerca(self.xogador):
                d = est.distancia_a(self.xogador)
                if d < menor:
                    menor = d
                    preto = est
        return preto

    #loxica para os highlights que fan de guia para a primeira tortilla
    def _highlight_activo(self):
        if self.primeira_tortilla_feita:
            return (None, None)

        man = self.man
        taboa = self.taboa
        fogon = self.Fogon
        cunca = self.cunca
        prato = self.prato

        if man and man.estado == TORTILLA:
            return (self.mostrador, "highlight_entrega.png")

        if (fogon.ingrediente_na_estacion and
                fogon.ingrediente_na_estacion.estado in (MESTURA_TORTILLA, TORTILLA)):
            return (fogon, "highlight_fritir.png")

        if man and man.estado == MESTURA_TORTILLA:
            return (fogon, "highlight_fritir.png")

        if cunca.mestura_lista:
            return (cunca, "highlight_bol.png")

        if man and man.estado == PATACA_FRITA:
            if cunca.ovo and cunca.ovo.estado == OVO_BATIDO:
                return (cunca, "highlight_bol.png")
            return (prato, "highlight_prato.png")

        if (cunca.ovo and cunca.ovo.estado == OVO_BATIDO and not cunca.pataca_frita):
            return (prato, "highlight_prato.png")

        if man and man.estado == OVO_ENTEIRO:
            return (cunca, "highlight_bol.png")

        if cunca.ovo and cunca.ovo.estado == OVO_ENTEIRO:
            return (cunca, "highlight_bol.png")

        if (prato.ingrediente_na_estacion and
                prato.ingrediente_na_estacion.estado == PATACA_FRITA and
                cunca.ovo is None):
            return (self.neveira, "highlight_ovos.png")

        if (fogon.ingrediente_na_estacion and
                fogon.ingrediente_na_estacion.estado == PATACA_FRITA and
                not fogon.cocinando):
            return (fogon, "highlight_fritir.png")

        if (fogon.cocinando and fogon.ingrediente_na_estacion and
                fogon.ingrediente_na_estacion.estado == PATACA_CORTADA):
            return (fogon, "highlight_fritir.png")

        if man and man.estado == PATACA_CORTADA:
            return (fogon, "highlight_fritir.png")

        if taboa.ingrediente_na_estacion:
            return (taboa, "highlight_cortar.png")

        if man and man.estado == PATACA_ENTEIRA:
            return (taboa, "highlight_cortar.png")

        return (self.caixa_patacas, "highlight_patacas.png")

    def _estacion_permitida(self, est):
        #durante a primeira tortilla, só se pode interactuar coa estación highlighteada.
        if self.primeira_tortilla_feita:
            return True
        est_guia, _ = self._highlight_activo()
        return est_guia is None or est is est_guia

    def accion_e(self):
        est = self._estacion_preto
        if est is None:
            return
        if not self._estacion_permitida(est):
            return

        if isinstance(est, Mostrador):
            if self.man and self.man.estado == TORTILLA:
                self.audio.reproducir_sonido("campana", self.audio.canal_accion)
                est.recibir_entrega(self.man)
                self.man = None
            return

        if self.man is not None:
            if isinstance(est, FonteIngrediente) and self.man.estado == est.tipo:
                self.audio.reproducir_sonido("dejar_item", self.audio.canal_accion)
                self.man = None
                return
            if isinstance(est, Cunca) and est.pode_recibir(self.man):
                self.audio.reproducir_sonido("dejar_item", self.audio.canal_accion)
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

        if est.pode_dar():
            if isinstance(est, FonteIngrediente):
                self.audio.reproducir_sonido("coger_item", self.audio.canal_accion)
                self.man = est.dar_ingrediente()
            else:
                self.man = est.ingrediente_na_estacion
                est.ingrediente_na_estacion = None
                if isinstance(est, Cunca):
                    est.mestura_lista = False
                self.audio.reproducir_sonido("coger_item", self.audio.canal_accion)

    def accion_x(self):
        if self._estacion_preto is not None:
            if not self._estacion_permitida(self._estacion_preto):
                return
            self._estacion_preto.accion_x(self.xogador)

    def eventos(self, lista_eventos):
        for evento in lista_eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_e:   self.accion_e()
                elif evento.key == pygame.K_x: self.accion_x()

    def update(self, tempo_ms):
        self._estacion_preto = self.get_estacion_preto()
        for est in self.estacions:
            est.update(tempo_ms)

    _HIGHLIGHTS_BAIXO_FRENTE = {
        "highlight_bol.png",
        "highlight_cortar.png",
        "highlight_patacas.png",
        "highlight_entrega.png",
    }

    def dibujar_highlight(self, pantalla, camara):
        est_guia, hl_nome = self._highlight_activo()
        if est_guia is not None and hl_nome not in self._HIGHLIGHTS_BAIXO_FRENTE:
            est_guia.dibujar(pantalla, camara, highlight_nome=hl_nome)

    def dibujar_highlight_frente(self, pantalla, camara):
        est_guia, hl_nome = self._highlight_activo()
        if est_guia is not None and hl_nome in self._HIGHLIGHTS_BAIXO_FRENTE:
            est_guia.dibujar(pantalla, camara, highlight_nome=hl_nome)

    def dibujar(self, pantalla, camara):
        #para as barras de progreso
        for est in self.estacions:
            est.dibujar(pantalla, camara)

        self.dibujar_hud(pantalla)

    def dibujar_hud(self, pantalla):
        fonte = _fonte(20, bold=True)

        txt_deuda = fonte.render(f"DEUDA: {self.deuda:.2f}€", True, (220, 40, 40))
        pantalla.blit(txt_deuda, (10, 10))

        txt_puntos = fonte.render(f"Tortillas: {self.puntos}", True, (255, 215, 0))
        pantalla.blit(txt_puntos, (10, 35))

        nome_man = self.man.nome() if self.man else "Baleira"
        txt_man  = fonte.render(f"Man: {nome_man}", True, COR_XOGADOR_HUD)
        pantalla.blit(txt_man, (10, 60))

        if self._estacion_preto:
            txt_est = fonte.render(
                f"[E] {self._estacion_preto.nome}  [X] Accion",
                True, (200, 255, 200)
            )
            pantalla.blit(txt_est, (10, 85))

    def _dibujar_sprite_estacion(self, pantalla, camara, sprite, rect, offset_x=0, offset_y=0):
        if sprite is None:
            return
        draw_x = rect.centerx - sprite.get_width() // 2 + offset_x
        draw_y = rect.centery - sprite.get_height() // 2 + offset_y
        pos = camara.aplicar_rect(pygame.Rect(draw_x, draw_y, 0, 0))
        pantalla.blit(sprite, (pos.x, pos.y))

    def dibujar_estaciones(self, pantalla, camara):
        # Sartén (Fogon): bajo la capa frente
        if self.Fogon.ingrediente_na_estacion is not None:
            sarten = _estacion_sprites.get("sarten_cocinando.png")
        else:
            sarten = _estacion_sprites.get("sarten.png")
        self._dibujar_sprite_estacion(pantalla, camara, sarten, self.Fogon.rect, offset_x=-7, offset_y=7)

    def dibujar_bol_frente(self, pantalla, camara):
        # Bol (Cunca): por encima de la capa frente
        if self.cunca.ovo is not None or self.cunca.pataca_frita is not None or self.cunca.mestura_lista:
            bol = _estacion_sprites.get("bol_mezcla.png")
        else:
            bol = _estacion_sprites.get("bol.png")
        self._dibujar_sprite_estacion(pantalla, camara, bol, self.cunca.rect, offset_x=0, offset_y=-6)

    def dibujar_item_en_man(self, pantalla, camara):
        if self.man is None:
            return
        sprite = _sprites_man.get(self.man.estado)
        if sprite is None:
            return

        # Calcular escala: el sprite del personaje es 16x16 antes de escalar
        pixel_scale = self.xogador.image.get_width() / 16

        # Pixel de la mano según dirección (11 mirando derecha, espejo 4 mirando izquierda)
        hand_px = 11 if self.xogador.facing_right else 4
        hand_world_x = self.xogador.rect.x + int(hand_px * pixel_scale)
        hand_world_y = self.xogador.rect.y + int(12 * pixel_scale)

        # Centrar el sprite del item en la mano
        mundo_x = hand_world_x - sprite.get_width() // 2
        mundo_y = hand_world_y - sprite.get_height() // 2

        pos = camara.aplicar_rect(pygame.Rect(mundo_x, mundo_y, 0, 0))
        pantalla.blit(sprite, (pos.x, pos.y))