# EJEMPLO 09: Sumar con "+=" (contador que va creciendo)
#
# "+=" quiere decir "sumale esto al valor que ya tenia". Es distinto a
# "=" (que reemplaza el valor). Aca, cada toque SUMA 1 a timesTouched,
# en vez de dejarlo siempre en 1.
#
# Tambien existe "-=" para restar, y mas adelante "*=" y "/=" para
# multiplicar y dividir (ejemplo 20).

entity Counter {
    timesTouched = 0

    on touch(player) {
        timesTouched += 1
    }
}
