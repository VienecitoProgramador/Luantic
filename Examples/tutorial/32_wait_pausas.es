# EJEMPLO 32: Pausar con "wait" (esperar segundos)
#
# "wait N" hace que el juego espere N segundos antes de seguir con la
# siguiente linea. Combinado con "repeat", sirve para efectos que se
# repiten con una pausa en el medio (como un faro que titila).

entity Beacon {
    on touch(player) {
        repeat 3 times {
            play "rbxassetid://5551234"
            wait 1
        }
    }
}
