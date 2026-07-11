# EJEMPLO 28: "const" (valores que nunca deberian cambiar)
#
# Cuando un numero es una regla fija del juego (por ejemplo, cuanto
# daño hace siempre una trampa, sin importar nada mas), usa "const" en
# vez de una propiedad normal. La diferencia: si por error intentas
# CAMBIAR una const mas adelante en el codigo, el compilador te avisa
# con un error, en vez de dejarte romper el balance del juego sin querer.

entity FireTrap {
    const Damage = 15

    on touch(player) {
        damage player Damage
    }
}
