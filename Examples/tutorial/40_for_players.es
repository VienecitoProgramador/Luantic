# EJEMPLO 40: "for player in players" (recorrer a todos los jugadores)
#
# Cuando necesitas hacer algo con CADA jugador conectado (no solo con
# uno), usas "for X in players { }". Adentro del bloque, "X" (aca le
# pusimos "player") representa a un jugador distinto en cada vuelta del
# recorrido, hasta pasar por todos.
#
# Se usa mucho junto con "on timer" para avisos periodicos a todos.

entity GameManager {
    @global

    on timer(seconds) {
        for player in players {
            message player "Seguis conectado, seguí jugando!"
        }
    }
}
