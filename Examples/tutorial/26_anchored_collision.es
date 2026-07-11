# EJEMPLO 26: "anchored" y "collision" (fisica basica)
#
# "anchored = true" significa que el objeto NO se cae por gravedad,
# queda flotando fijo donde lo pusiste. Sin esto, cualquier parte cae al
# piso apenas arranca el juego.
#
# "collision = false" significa que los jugadores pueden ATRAVESAR el
# objeto caminando, en vez de chocar contra el como una pared solida.
# Es tipico en monedas y power-ups: se ven, pero no bloquean el paso.

entity FloatingCoin {
    position = (0, 5, 0)
    anchored = true
    collision = false
}
