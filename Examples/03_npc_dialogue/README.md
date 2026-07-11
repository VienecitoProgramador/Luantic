# Ejemplo 03: NPC con dialogo, interaccion y loop

Demuestra:
- Comentario de bloque (`### ... ###`) documentando una decision de
  produccion (modelo temporal), no "que hace el codigo".
- `on interact(player)` conectado a un `ProximityPrompt` de Roblox
  automaticamente por el Runtime.
- `on timer(seconds)` para logica periodica.
- `repeat N times { ... }` como unica forma de expresar loops acotados en v0.1.

Este ejemplo se usa tambien en `Tests/transpiler_tests/` como golden file
para validar la traduccion de `repeat` a un `for` Luau.
