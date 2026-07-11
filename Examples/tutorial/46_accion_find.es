# EJEMPLO 46: "find" (buscar todas las copias de una entidad)
#
# "find NombreDeEntidad" busca en todo el mapa y devuelve todas las
# instancias que existen de esa entidad en ese momento. Es util para
# saber, por ejemplo, cuantas monedas quedan sin recolectar.

entity ProgressChecker {
    @global

    on timer(seconds) {
        find Coin
    }
}
