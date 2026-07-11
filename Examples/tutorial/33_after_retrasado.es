# EJEMPLO 33: "after" (hacer algo una sola vez, mas tarde)
#
# "after N { }" ejecuta lo de adentro una UNICA vez, despues de esperar
# N segundos, sin bloquear el resto del juego mientras tanto (a
# diferencia de "wait", que pausa la ejecucion en el momento). Es ideal
# para cosas como "la moneda vuelve a aparecer a los 5 segundos".

entity RespawningCoin {
    on touch(player) {
        destroy self

        after 5 {
            print "Aca reaparecería la moneda"
        }
    }
}
