# EJEMPLO 44: "message" a un jugador especifico vs a todos
#
# "message player texto" le muestra el mensaje SOLO al jugador que
# disparo el evento (por ejemplo, el que toco el objeto).
# "message all texto" le muestra el mismo mensaje a TODOS los
# jugadores conectados al servidor, no solo a uno.

entity PersonalAlarm {
    on touch(player) {
        message player "Vos activaste la alarma"
    }
}

entity ServerWideAlarm {
    on touch(player) {
        message all "Alguien activo la alarma del servidor!"
    }
}
