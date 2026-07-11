# EJEMPLO 16: Conectar una entidad a un leaderstat con "score"
#
# Ahora que existe el marcador "Coins" (ejemplo 15), hay que decirle a
# la moneda A CUAL marcador debe sumar puntos. Eso se hace con
# "score = Coins" dentro de la entidad.
#
# A partir de ahi, "give player value" ya sabe automaticamente que tiene
# que sumarle a "Coins" en el marcador visible del jugador.

leaderstat Coins = 0

entity GoldCoin {
    value = 10
    score = Coins

    on touch(player) {
        give player value
        destroy self
    }
}
