# EJEMPLO 39: "on leave" y "on death" (mas eventos globales)
#
# Ademas de "on join", las entidades @global tienen otros dos eventos
# de jugador disponibles:
#   - on leave(player)  -> cuando alguien SE VA del juego
#   - on death(player)  -> cuando el personaje de alguien MUERE
#
# Los tres (join, leave, death) solo existen dentro de @global, igual
# que vimos en el ejemplo 38.

entity GameManager {
    @global

    on leave(player) {
        print "Un jugador se desconecto"
    }

    on death(player) {
        message player "Moriste! Vas a reaparecer en un momento"
    }
}
