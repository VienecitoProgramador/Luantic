# EJEMPLO 31: Repetir una accion varias veces con "repeat"
#
# "repeat N times { }" ejecuta lo que esta adentro N veces seguidas. Es
# la unica forma de hacer loops en EntityScript v0.2: simple a proposito,
# para cubrir el caso mas comun (repetir algo un numero fijo de veces).

entity Firework {
    on touch(player) {
        repeat 3 times {
            play "rbxassetid://5551234"
        }
    }
}
