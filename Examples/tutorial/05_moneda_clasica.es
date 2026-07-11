# EJEMPLO 05: La moneda clasica (propiedad + evento + accion)
#
# Este es el ejemplo mas famoso de EntityScript: una moneda que da
# puntos y desaparece. Combina todo lo visto hasta ahora:
#   - una propiedad (value)
#   - un evento (on touch)
#   - dos acciones dentro del evento (give y destroy)
#
# "give player value" significa "dale al jugador la cantidad que dice
# la propiedad value". Todavia no suma a un marcador visible en pantalla
# (eso viene en el ejemplo 15 con "leaderstat"), pero ya es la base de
# cualquier sistema de recompensas.

entity Coin {
    value = 10

    on touch(player) {
        give player value
        destroy self
    }
}
