# EJEMPLO 07: Evento "on click" (cuando el jugador hace clic)
#
# A diferencia de "on touch" (que necesita que el personaje choque
# fisicamente contra el objeto), "on click" se dispara cuando el
# jugador hace clic con el mouse sobre el objeto, sin necesidad de
# acercarse. Sirve para botones, palancas, interruptores.

entity Lever {
    on click(player) {
        print "Alguien acciono la palanca"
    }
}
