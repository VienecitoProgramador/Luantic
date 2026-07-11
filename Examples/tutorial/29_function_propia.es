# EJEMPLO 29: Tu primera "function" (evitar repetir codigo)
#
# Cuando la misma logica se necesita en mas de un lugar dentro de la
# MISMA entidad, la podes guardar en una "function" con un nombre
# propio, y despues llamarla desde donde haga falta escribiendo su
# nombre seguido de parentesis: Collect(player).
#
# Esto evita copiar y pegar las mismas lineas dos veces.

entity TreasureChest {
    value = 100

    function Collect(player) {
        give player value
        destroy self
    }

    on touch(player) {
        Collect(player)
    }
}
