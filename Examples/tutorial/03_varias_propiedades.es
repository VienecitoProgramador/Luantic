# EJEMPLO 03: Varias propiedades, varios tipos
#
# Una entidad puede tener todas las propiedades que necesites. Aca hay
# tres tipos distintos, y el compilador los detecta solo:
#   - numero        -> 100
#   - texto         -> "Espada de fuego"
#   - verdadero/falso -> true / false

entity Sword {
    damage = 25
    name = "Espada de fuego"
    isMagic = true
}
