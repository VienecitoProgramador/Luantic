# Este es el ejemplo canonico del design doc: reduccion de ~28 lineas
# de Luau verboso a 7 lineas declarativas.
entity Coin {
    points: Number = 10
    sound: Sound = "rbxassetid://1234567"

    on touch(player) {
        give player points
        play sound
        destroy self
    }
}
