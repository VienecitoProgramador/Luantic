# EJEMPLO 38: Entidades "@global" y el evento "on join"
#
# Hasta ahora todas las entidades representaban objetos fisicos del
# mapa (monedas, puertas, cofres). Pero algunos eventos no tienen que
# ver con un objeto, sino con el JUEGO entero: por ejemplo, "alguien
# entro a la partida". Para estos casos existe el tag "@global", que
# convierte la entidad en un "director" de logica de juego en vez de un
# objeto fisico.
#
# "on join(player)" SOLO funciona dentro de una entidad @global: no
# tiene sentido que una moneda "escuche" cuando alguien entra al juego.

entity GameManager {
    @global

    on join(player) {
        message player "Bienvenido al servidor!"
    }
}
