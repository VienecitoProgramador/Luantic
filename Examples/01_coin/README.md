# Ejemplo 01: Coin

El ejemplo mas simple de EntityScript: una moneda que da puntos y se
autodestruye al ser tocada por un jugador.

Compilar:

```bash
python CLI/es_build.py Examples/01_coin/coin.es --out Examples/01_coin/build
```

Esto genera `Examples/01_coin/build/Coin.luau`, listo para pegar como
`Script` dentro de la parte que representa la moneda en Roblox Studio.

Ver la comparativa completa (Luau escrito a mano vs este archivo) en
`Docs/language_spec.md`, seccion 4.
