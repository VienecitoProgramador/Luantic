# EJEMPLO 43: "teleport" (mover al jugador de lugar al instante)
#
# "teleport player Destino" mueve al jugador de forma instantanea hasta
# el objeto que le indiques por nombre. El nombre debe coincidir con el
# nombre de una entidad o parte que exista en tu mapa.

entity MagicPortal {
    on touch(player) {
        teleport player Spawn
    }
}
