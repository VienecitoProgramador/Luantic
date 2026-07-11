# EJEMPLO 11: Tu primer "if" (decisiones en el codigo)
#
# "if" te deja decidir: "SI se cumple esto, hace lo de adentro". Aca,
# solo si la vida llega a 0 o menos, se destruye la entidad. Si la vida
# esta por encima de 0, no pasa nada.
#
# "<=" significa "menor o igual que". Tambien existen: > (mayor), <
# (menor), >= (mayor o igual), == (igual), != (distinto).

entity Barrel {
    health = 30

    on damage(amount, source) {
        health -= amount

        if health <= 0 {
            destroy self
        }
    }
}
