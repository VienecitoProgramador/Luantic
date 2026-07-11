# EJEMPLO 37: Tag "@respawnable" (que vuelva a aparecer solo)
#
# "@respawnable(N)" marca la entidad para que, tras ser destruida,
# vuelva a aparecer automaticamente despues de N segundos. Es la forma
# recomendada de hacer monedas, power-ups o enemigos que se regeneran
# con el tiempo.

entity RegeneratingGem {
    @respawnable(15)

    on touch(player) {
        destroy self
    }
}
