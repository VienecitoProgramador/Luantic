# EJEMPLO 02: Agregar una propiedad
#
# Las entidades pueden tener propiedades (datos que guardan). Se escriben
# como "nombre = valor". No hace falta decir de que tipo es: el compilador
# lo adivina solo mirando el valor (10 es un numero, "hola" es texto, etc).
#
# Esto se llama "inferencia de tipos" y es una de las cosas que hace que
# EntityScript sea mas corto de escribir que Luau puro.

entity Rock {
    weight = 50
}
