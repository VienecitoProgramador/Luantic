# EJEMPLO 17: Dos marcadores distintos en el mismo juego
#
# Un juego puede tener varios leaderstats a la vez (por ejemplo, monedas
# Y victorias). Cada entidad elige a cual de los dos conectarse con
# "score = NombreDelMarcador".

leaderstat Coins = 0
leaderstat Gems = 0

entity CopperCoin {
    value = 5
    score = Coins

    on touch(player) {
        give player value
        destroy self
    }
}

entity Diamond {
    value = 1
    score = Gems

    on touch(player) {
        give player value
        destroy self
    }
}
