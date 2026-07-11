# EJEMPLO 14: Herencia con "extends" (compartir propiedades entre entidades)
#
# Cuando varias entidades comparten propiedades (por ejemplo, todos los
# personajes tienen vida), podes declarar una entidad base UNA VEZ y que
# las demas "extiendan" de ella con "extends". Character define health,
# y Zombie lo usa sin tener que volver a escribirlo.
#
# Esto evita repetir el mismo codigo en cada enemigo que crees.

entity Character {
    health = 100
}

entity Zombie extends Character {
    on damage(amount, source) {
        health -= amount
    }
}
