# EJEMPLO 41: "heal" y "damage" (curar y hacer daño a un jugador)
#
# "heal player N" le suma N de vida al personaje del jugador.
# "damage player N" le resta N de vida.
# Ambas acciones afectan la barra de vida REAL de Roblox (la que se ve
# en pantalla), no una propiedad inventada.

entity HealingPotion {
    const HealAmount = 25

    on touch(player) {
        heal player HealAmount
        destroy self
    }
}

entity PoisonSpike {
    const PoisonDamage = 10

    on touch(player) {
        damage player PoisonDamage
    }
}
