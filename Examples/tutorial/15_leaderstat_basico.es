# EJEMPLO 15: Leaderstat (el marcador de puntos que se ve en pantalla)
#
# "leaderstat" crea un marcador REAL que Roblox muestra automaticamente
# en la lista de jugadores (arriba a la derecha del juego). Se declara
# UNA VEZ, fuera de cualquier entidad, al principio del archivo.
#
# "leaderstat Coins = 0" crea un marcador llamado "Coins" que arranca
# en 0 para cada jugador que entra al juego.

leaderstat Coins = 0

entity GoldCoin {
    on touch(player) {
        print "Toco la moneda"
    }
}
