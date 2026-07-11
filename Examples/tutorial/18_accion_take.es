# EJEMPLO 18: "take" (quitar puntos en vez de darlos)
#
# Asi como "give" suma puntos al marcador, "take" los resta. Sirve para
# trampas, penalizaciones, o objetos que le cuestan algo al jugador.

leaderstat Coins = 0

entity SpikeTrap {
    penalty = 5
    score = Coins

    on touch(player) {
        take player penalty
        message player "Perdiste monedas por pisar la trampa"
    }
}
