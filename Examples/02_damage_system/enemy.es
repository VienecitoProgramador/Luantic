use Combat.Character

# Los goblins son enemigos basicos: poca vida, sin loot especial.
# Extienden Character (importado desde Combat/Character.es) para heredar `health`.
entity Goblin extends Character {
    @respawnable(15)

    on spawn {
        health = maxHealth
    }

    on damage(amount, source) {
        health -= amount

        if health <= 0 {
            emit EnemyDefeated(self)
            destroy self
        } else {
            play "rbxassetid://9990001"
        }
    }
}
