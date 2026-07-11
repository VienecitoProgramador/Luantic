# EJEMPLO 04: Tu primer evento (on touch)
#
# Un "evento" es algo que responde cuando pasa algo en el juego.
# "on touch(player)" significa: "cuando un jugador toque esto, hace lo
# de adentro". Dentro de las llaves { } van las acciones a ejecutar.
#
# "destroy self" es una accion: "destruime a mi mismo (el objeto)".

entity Bubble {
    on touch(player) {
        destroy self
    }
}
