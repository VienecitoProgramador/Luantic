leaderstat Coins = 0
leaderstat Wins = 0

entity Coin {
    const RespawnDelay = 3
    value = 10
    score = Coins

    position = (0, 3, 0)
    color = "#FFD700"
    anchored = true
    collision = false

    function Collect(player) {
        give player value
        destroy self
    }

    on touch(player) {
        Collect(player)
    }
}

entity GameManager {
    @global

    on join(player) {
        message player "Bienvenido al juego!"
    }

    on timer(seconds) {
        for player in players {
            message player "Sigue jugando!"
        }
    }
}
