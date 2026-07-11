# Ejemplo 04: Leaderstats, funciones propias y eventos globales (v0.2)

Demuestra todas las features nuevas de v0.2:

- `leaderstat Coins = 0` — declara un stat de jugador (Folder + IntValue generado automaticamente)
- `score = Coins` — vincula esta entidad al leaderstat `Coins`, para que `give`/`take`/`set` sepan a cual stat modificar
- `const RespawnDelay = 3` — constante, error de compilacion si se reasigna
- Inferencia de tipos: `value = 10` en vez de `value: Number = 10`
- `function Collect(player) { ... }` — logica reutilizable dentro de la entidad
- Propiedades fisicas: `position`, `color` (con hex `"#FFD700"`), `anchored`, `collision`
- `entity GameManager { @global ... }` — entidad de logica de servidor, unica forma de usar `on join`
- `for player in players { ... }` — iterar sobre todos los jugadores conectados

Compilar:

```bash
python CLI/es_build.py Examples/04_leaderstats_and_functions/game.es --out Examples/04_leaderstats_and_functions/build
```

Esto genera:
- `LeaderstatsSetup.luau` — pegar en `ServerScriptService` (una sola vez por juego)
- `Coin.luau` — pegar como `Script` dentro de la parte que representa la moneda
- `GameManager.luau` — pegar como `Script` en `ServerScriptService`
