# EJEMPLO 34: "on timer" (repetir algo cada cierto tiempo, para siempre)
#
# A diferencia de "after" (que se ejecuta UNA vez), "on timer" se repite
# SOLO por si mismo cada cierto intervalo, sin que tengas que llamarlo.
# Por defecto, el intervalo es de 1 segundo, hasta que uses el tag
# "@interval" (ejemplo 35) para cambiarlo.

entity Fountain {
    on timer(seconds) {
        print "La fuente sigue andando"
    }
}
