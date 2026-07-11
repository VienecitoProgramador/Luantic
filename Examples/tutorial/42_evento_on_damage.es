# EJEMPLO 42: El EVENTO "on damage" (distinto de la ACCION "damage")
#
# Cuidado con esta diferencia importante: la accion "damage" (ejemplo
# 41) hace daño a algo. El EVENTO "on damage(amount, source)" es algo
# totalmente distinto: se dispara cuando ESTA entidad recibe daño desde
# afuera, y te deja reaccionar a eso (por ejemplo, destruirse si la
# vida llega a 0).
#
# Son dos herramientas separadas que no se activan una a la otra
# automaticamente.

entity Zombie {
    health = 50

    on damage(amount, source) {
        health -= amount

        if health <= 0 {
            destroy self
        }
    }
}
