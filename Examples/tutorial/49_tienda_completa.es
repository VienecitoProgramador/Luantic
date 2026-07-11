# EJEMPLO 49: Sistema de tienda completo (combina muchos conceptos juntos)
#
# Este ejemplo junta varias piezas que ya viste por separado, para que
# veas como se combinan en un caso mas real:
#   - leaderstat + score       (ejemplos 15, 16)
#   - const                    (ejemplo 28)
#   - function                 (ejemplo 29)
#   - if / else                (ejemplo 12)
#   - message                  (ejemplo 44)
#   - propiedades fisicas      (ejemplos 21-27)

leaderstat Coins = 0

entity ShopKeeper {
    const SwordPrice = 50
    const ShieldPrice = 30
    score = Coins

    position = (0, 3, 0)
    color = purple
    anchored = true

    function SellSword(player) {
        take player SwordPrice
        message player "Compraste una espada!"
    }

    function SellShield(player) {
        take player ShieldPrice
        message player "Compraste un escudo!"
    }

    on interact(player) {
        message player "Bienvenido a la tienda. Toca de nuevo para comprar una espada."
    }

    on touch(player) {
        SellSword(player)
    }
}
