# EJEMPLO 06: Evento "on spawn" (cuando el objeto aparece)
#
# "on spawn" se ejecuta una sola vez, apenas el objeto existe en el
# juego (cuando arranca la partida, o cuando el objeto se crea). Es util
# para preparar cosas antes de que un jugador interactue.
#
# "print" muestra un mensaje en la consola de Roblox Studio (Output).
# Es la herramienta principal para revisar que tu codigo esta corriendo
# bien mientras programas.

entity Lantern {
    on spawn {
        print "La linterna esta lista"
    }
}
