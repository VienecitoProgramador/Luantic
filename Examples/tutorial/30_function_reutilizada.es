# EJEMPLO 30: Una funcion usada desde DOS eventos distintos
#
# Aca se ve para que sirve de verdad una "function": la misma logica de
# "abrir la puerta" se necesita tanto si el jugador toca la puerta como
# si hace clic en ella. En vez de escribir "isOpen = true" y el mensaje
# dos veces, se escribe una sola vez en la funcion Open, y se llama
# desde los dos eventos.

entity AutoDoor {
    isOpen = false

    function Open(player) {
        isOpen = true
        message player "La puerta se abrio"
    }

    on touch(player) {
        Open(player)
    }

    on click(player) {
        Open(player)
    }
}
