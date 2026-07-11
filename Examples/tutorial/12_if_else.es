# EJEMPLO 12: "if" con "else" (dos caminos posibles)
#
# "else" agrega un segundo camino: "si NO se cumplio la condicion,
# hace esto otro en cambio". Solo uno de los dos bloques se ejecuta,
# nunca ambos.

entity VIPDoor {
    on touch(player) {
        if player.isAdmin {
            message player "Bienvenido, administrador"
        } else {
            message player "No tenes permiso para entrar"
        }
    }
}
