# EJEMPLO 20: Multiplicar y dividir con "*=" y "/="
#
# Igual que "+=" suma y "-=" resta, "*=" multiplica y "/=" divide el
# valor actual de una propiedad. Sirve para efectos como "velocidad
# duplicada" o "daño reducido a la mitad".

entity SpeedBoost {
    speed = 16

    on touch(player) {
        speed *= 2
        message player "Tu velocidad se duplico!"
    }
}

entity Shield {
    incomingDamage = 20

    on touch(player) {
        incomingDamage /= 2
        message player "El daño que recibis se redujo a la mitad"
    }
}
