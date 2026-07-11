# EJEMPLO 35: Cambiar cada cuanto se repite el timer con "@interval"
#
# Los "tags" son etiquetas especiales que empiezan con @ y agregan
# comportamiento extra a una entidad. "@interval(N)" le dice al timer
# que se repita cada N segundos, en vez del valor por defecto (1 segundo).
#
# Aca, el mensaje va a aparecer cada 10 segundos, no cada 1.

entity SlowFountain {
    @interval(10)

    on timer(seconds) {
        print "Han pasado 10 segundos"
    }
}
