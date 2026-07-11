# EJEMPLO 47: "emit" (avisar a otras entidades que paso algo)
#
# "emit NombreDeEvento" lanza un aviso propio, inventado por vos, que
# otras partes del juego pueden "escuchar" si estan preparadas para
# eso. Sirve para desacoplar sistemas: por ejemplo, cuando un enemigo
# muere, "emite" que murio, y un sistema de puntaje o de logros puede
# reaccionar a eso sin que el enemigo sepa nada de logros.

entity Goblin {
    health = 30

    on damage(amount, source) {
        health -= amount

        if health <= 0 {
            emit EnemyDefeated(self)
            destroy self
        }
    }
}
