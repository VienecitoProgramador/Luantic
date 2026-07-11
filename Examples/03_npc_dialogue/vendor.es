### 
Este NPC usa un modelo temporal proporcionado por el equipo de arte.
Reemplazar antes del lanzamiento -- ticket ART-221.
###
entity NPCVendor {
    greetCount: Number = 0

    on interact(player) {
        greetCount += 1
        print "Bienvenido al mercado, viajero."

        if greetCount > 3 {
            give player 5
        }
    }

    on timer(seconds) {
        repeat 2 times {
            play "rbxassetid://5551234"
            wait 1
        }
    }
}
