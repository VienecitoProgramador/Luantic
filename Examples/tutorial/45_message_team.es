# EJEMPLO 45: "message team" (avisar solo a un equipo)
#
# Si tu juego tiene equipos configurados en Roblox (por ejemplo "Rojo" y
# "Azul"), "message team NombreDelEquipo texto" le avisa unicamente a
# los jugadores de ESE equipo, sin molestar al resto.

entity RedTeamFlag {
    on touch(player) {
        message team Red "Tu equipo capturo la bandera!"
    }
}
