# EJEMPLO 19: "set" (poner el marcador en un numero exacto)
#
# A diferencia de "give"/"take" (que suman o restan), "set" pone el
# marcador directamente en el numero que le digas, sin importar cuanto
# tenia antes. Util para resetear puntajes o premios especiales que
# fijan un valor concreto.

leaderstat Coins = 0

entity JackpotChest {
    score = Coins

    on touch(player) {
        set player 1000
        message player "Ganaste el premio mayor!"
    }
}
