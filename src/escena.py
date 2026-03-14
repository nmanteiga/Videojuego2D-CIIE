# tamanño de la ventana
ANCHO = 800
ALTO = 600

# plantilla base para las dmas escenas (no tocar)
class Escena:
    
    def __init__(self, director):
        self.director = director
    
    def update(self, *args):
        raise NotImplemented("Falta implementar el metodo update.")
    
    def eventos(self, *args):
        raise NotImplemented("Falta implementar el metodo eventos.")
    
    def dibujar(self, pantalla):
        raise NotImplemented("Falta implementar el metodo dibujar.")