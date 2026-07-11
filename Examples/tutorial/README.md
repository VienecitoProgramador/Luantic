# Tutorial de EntityScript: 50 ejemplos progresivos

Cada archivo `.es` de esta carpeta enseña **un concepto nuevo**, en
orden de dificultad creciente. Todos compilan de verdad (`python3
CLI/es_build.py Examples/tutorial/NN_nombre.es --out /tmp/salida`) y
tienen comentarios explicando qué hacen y por qué.

No hace falta leerlos todos de una sentada. La idea es: cuando quieras
usar una feature del lenguaje y no te acuerdes bien la sintaxis, buscá
el ejemplo que la enseña y copiá el patrón.

## Bloque 1 — Fundamentos (01-10)

| # | Archivo | Qué enseña |
|---|---|---|
| 01 | `01_entidad_vacia.es` | Qué es una `entity`, la unidad básica de todo |
| 02 | `02_propiedad_simple.es` | Agregar una propiedad con inferencia de tipo |
| 03 | `03_varias_propiedades.es` | Número, texto y booleano en una misma entidad |
| 04 | `04_primer_evento.es` | Tu primer `on touch` + acción `destroy` |
| 05 | `05_moneda_clasica.es` | El ejemplo canónico: moneda que da puntos |
| 06 | `06_evento_spawn.es` | `on spawn`, se ejecuta al aparecer el objeto |
| 07 | `07_evento_click.es` | `on click`, interacción a distancia |
| 08 | `08_modificar_propiedad.es` | Reasignar una propiedad con `=` |
| 09 | `09_operador_mas_igual.es` | `+=` para sumar sin reemplazar |
| 10 | `10_comentarios_bloque.es` | Comentarios de bloque `### ... ###` |

## Bloque 2 — Decisiones y estructura (11-20)

| # | Archivo | Qué enseña |
|---|---|---|
| 11 | `11_condicional_if.es` | `if` básico |
| 12 | `12_if_else.es` | `if` / `else` |
| 13 | `13_comparacion_igual.es` | `==` vs `=`, la diferencia crítica |
| 14 | `14_herencia_extends.es` | `extends`, compartir propiedades |
| 15 | `15_leaderstat_basico.es` | `leaderstat`, marcador visible en pantalla |
| 16 | `16_conectar_score.es` | `score = X`, conectar entidad a leaderstat |
| 17 | `17_dos_leaderstats.es` | Múltiples marcadores en un mismo juego |
| 18 | `18_accion_take.es` | `take`, restar puntos |
| 19 | `19_accion_set.es` | `set`, fijar un valor exacto |
| 20 | `20_multiplicar_dividir.es` | `*=` y `/=` |

## Bloque 3 — Apariencia y organización (21-30)

| # | Archivo | Qué enseña |
|---|---|---|
| 21 | `21_posicion.es` | `position`, ubicar en el mundo 3D |
| 22 | `22_posicion_negativa.es` | Números negativos en posiciones |
| 23 | `23_tamano_size.es` | `size`, dimensiones del objeto |
| 24 | `24_color_nombre.es` | `color` con nombre reservado |
| 25 | `25_color_hexadecimal.es` | `color` con código hex `"#RRGGBB"` |
| 26 | `26_anchored_collision.es` | `anchored` y `collision`, física básica |
| 27 | `27_transparencia.es` | `transparency`, objetos semi-invisibles |
| 28 | `28_const_valores_fijos.es` | `const`, valores que no deben cambiar |
| 29 | `29_function_propia.es` | Tu primera `function` reutilizable |
| 30 | `30_function_reutilizada.es` | Una función llamada desde dos eventos |

## Bloque 4 — Tiempo y eventos globales (31-40)

| # | Archivo | Qué enseña |
|---|---|---|
| 31 | `31_repeat_times.es` | `repeat N times`, loops |
| 32 | `32_wait_pausas.es` | `wait`, pausar dentro de un evento |
| 33 | `33_after_retrasado.es` | `after N`, ejecutar algo una vez, más tarde |
| 34 | `34_timer_basico.es` | `on timer`, repetición automática |
| 35 | `35_tag_interval.es` | `@interval(N)`, configurar el timer |
| 36 | `36_tag_locked.es` | Tag `@locked` |
| 37 | `37_tag_respawnable.es` | Tag `@respawnable(N)` |
| 38 | `38_global_on_join.es` | `@global` y `on join`, lógica de servidor |
| 39 | `39_leave_death.es` | `on leave` y `on death` |
| 40 | `40_for_players.es` | `for player in players`, recorrer a todos |

## Bloque 5 — Acciones avanzadas e integración (41-50)

| # | Archivo | Qué enseña |
|---|---|---|
| 41 | `41_heal_damage.es` | `heal` y `damage`, vida real de Roblox |
| 42 | `42_evento_on_damage.es` | El evento `on damage` (≠ la acción `damage`) |
| 43 | `43_teleport.es` | `teleport`, mover al jugador |
| 44 | `44_message_player_vs_all.es` | `message player` vs `message all` |
| 45 | `45_message_team.es` | `message team`, avisar solo a un equipo |
| 46 | `46_accion_find.es` | `find`, buscar entidades por nombre |
| 47 | `47_emit_eventos_custom.es` | `emit`, eventos propios entre entidades |
| 48 | `48_import_use.es` | `use`, importar entidades de otro archivo |
| 49 | `49_tienda_completa.es` | Sistema de tienda combinando varios conceptos |
| 50 | `50_minijuego_completo.es` | Mini-juego completo, cierre del recorrido |

## Cómo probarlos

Con la app de escritorio (`Editor/desktop_app.py`), abrí cualquiera de
estos archivos con **Archivo → Abrir .es...** y mirá el Luau que
genera en el panel derecho.

O por línea de comandos:

```bash
python3 CLI/es_build.py Examples/tutorial/05_moneda_clasica.es --out /tmp/salida
cat /tmp/salida/Coin.luau
```

El ejemplo 48 (`48_import_use.es`) depende de `Shared/Character.es` en
esta misma carpeta — no lo muevas a otro lado sin mover también esa
subcarpeta.
