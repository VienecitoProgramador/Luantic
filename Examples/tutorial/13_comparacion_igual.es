# EJEMPLO 13: Comparar con "==" (verificar que algo sea exactamente igual)
#
# "==" (dos signos igual) pregunta "es esto igual a esto otro?", a
# diferencia de "=" (un solo signo) que ASIGNA un valor. Es un error muy
# comun confundirlos en casi todos los lenguajes de programacion, por
# eso EntityScript los mantiene bien distintos: "=" para asignar,
# "==" para comparar.

entity SecretDoor {
    isOpen = false

    on touch(player) {
        if isOpen == false {
            isOpen = true
            message player "La puerta se abrio"
        }
    }
}
