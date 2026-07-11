# EJEMPLO 08: Cambiar el valor de una propiedad
#
# Dentro de un evento, podes cambiar el valor de una propiedad usando
# "=". Aca, cada vez que alguien toca la entidad, "timesTouched" cambia
# de 0 a 1.
#
# Ojo: esto SIEMPRE pone timesTouched en 1, no lo va sumando. Para sumar
# de a poco, el ejemplo 09 muestra "+=".

entity Switch {
    timesTouched = 0

    on touch(player) {
        timesTouched = 1
    }
}
