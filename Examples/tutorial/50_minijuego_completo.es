# EJEMPLO 50: Mini-juego completo (el resumen de todo el recorrido)
#
# Llegaste al final del tutorial! Este ultimo ejemplo es un mini-juego
# jugable de verdad, que usa casi todos los conceptos que viste en los
# 49 ejemplos anteriores, todos trabajando juntos:
#
#   leaderstat, score, const, function, herencia (extends), @global,
#   @respawnable, on join, on timer, for players, if/else, heal, damage,
#   teleport, message, propiedades fisicas, colores, operadores +=/-=.
#
# No hace falta que entiendas cada linea de una sola leida: la idea es
# que reconozcas los pedacitos, porque ya los viste antes, uno por uno.

leaderstat Coins = 0
leaderstat Wins = 0

entity Character {
    health = 100
    maxHealth = 100
}

entity Coin {
    const Value = 10
    score = Coins

    position = (0, 3, 0)
    color = yellow
    anchored = true
    collision = false

    @respawnable(8)

    function Collect(player) {
        give player Value
        destroy self
    }

    on touch(player) {
        Collect(player)
    }
}

entity HealFountain {
    const HealAmount = 30

    position = (10, 3, 0)
    color = green
    anchored = true

    on touch(player) {
        heal player HealAmount
        message player "Te curaste en la fuente"
    }
}

entity Enemy extends Character {
    const AttackDamage = 15

    color = red
    anchored = false

    on touch(player) {
        damage player AttackDamage
    }

    on damage(amount, source) {
        health -= amount

        if health <= 0 {
            emit EnemyDefeated(self)
            destroy self
        }
    }
}

entity FinishLine {
    on touch(player) {
        set player 1
        teleport player Spawn
        message all "Un jugador termino el recorrido!"
    }
}

entity GameManager {
    @global

    on join(player) {
        message player "Bienvenido! Recolecta monedas y llega a la meta."
    }

    on timer(seconds) {
        for player in players {
            message player "Seguí explorando el mapa!"
        }
    }
}
