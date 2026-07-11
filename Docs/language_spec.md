# EntityScript — Especificación del Lenguaje (v0.1)

EntityScript (ES) es un DSL orientado a entidades y eventos que transpila a
Luau para el desarrollo de videojuegos en Roblox.

Este documento es la referencia completa de la sintaxis. Para la arquitectura
del compilador, ver [`architecture.md`](./architecture.md). Para la
justificación de cada decisión de diseño, ver [`philosophy.md`](./philosophy.md).

## 1. Instalación y primer uso

```bash
git clone <repo>
cd entityscript
python3 CLI/es_init.py mi_juego
python3 CLI/es_build.py mi_juego/src/main.es --out mi_juego/build
```

Esto genera `mi_juego/build/Coin.luau`, listo para pegar en Roblox Studio.

## 2. Sintaxis básica

### 2.1 Entidades

```
entity Coin {
    points: Number = 10
}
```

- El nombre de la entidad **debe** ser PascalCase.
- Cada propiedad se traduce a un Roblox Instance Attribute (`self:SetAttribute`),
  visible y editable desde el panel Properties de Roblox Studio.

### 2.2 Herencia

```
entity Character {
    health: Number = 100
}

entity Goblin extends Character {
    on damage(amount) {
        health -= amount
    }
}
```

`Goblin` puede usar `health` sin redeclararlo. El compilador valida en tiempo
de compilación que la propiedad existe en la cadena de herencia.

### 2.3 Eventos

| Evento ES | Señal Roblox equivalente |
|---|---|
| `touch` | `BasePart.Touched` (con debounce y resolución de Player automáticas) |
| `spawn` | Ejecución inmediata al iniciar el script |
| `destroy` | `Instance.AncestryChanged` (detecta remoción del árbol) |
| `click` | `ClickDetector.MouseClick` |
| `damage` | `BindableEvent` custom (`ESDamageEvent`) |
| `interact` | `ProximityPrompt.Triggered` |
| `timer` | Bucle periódico vía `task.spawn` |

```
on touch(player) {
    destroy self
}
```

### 2.4 Tags declarativos

```
entity Door {
    @locked
    @respawnable(10)
}
```

Tags conocidos en v0.1: `@locked`, `@respawnable(segundos)`, `@serverOnly`,
`@clientOnly`.

### 2.5 Sentencias

```
health -= 10           # asignación compuesta
give player points     # llamada de acción (sin paréntesis)
play sound
destroy self

if health <= 0 {       # condicional
    destroy self
} else {
    play "sound"
}

repeat 3 times {        # loop acotado
    wait 1
}

emit ScoreChanged(self, points)   # evento custom entre entidades
```

### 2.6 Comentarios

```
# Comentario de una línea

###
Comentario de bloque,
puede ocupar varias líneas.
###
```

**Guía de uso** (ver `philosophy.md` para el razonamiento completo):
un comentario es útil cuando documenta **por qué**, no **qué**. El linter de
comentarios (`Compiler/Semantic/comment_linter.py`) emite advertencias
(nunca errores) cuando detecta comentarios que repiten el nombre del
identificador siguiente.

### 2.7 Imports entre archivos (`use`)

```
use Combat.Character

entity Goblin extends Character {
    ...
}
```

`use Combat.Character` busca, relativo al archivo actual, `Combat/Character.es`
(o `Combat.Character.es` como fallback plano). El resolutor
(`Compiler/Semantic/module_resolver.py`) fusiona las entidades del módulo
importado en el `Program` antes del type-check, por lo que `extends` funciona
igual entre archivos que dentro del mismo archivo. Ver ejemplo completo en
`Examples/02_damage_system/`.

Errores relacionados:

| Error | Causa |
|---|---|
| `ModuleNotFound` | La ruta de `use` no corresponde a ningún archivo `.es` |
| `CircularImport` | `A` importa `B` y `B` importa `A` (directa o transitivamente) |


Ver la gramática completa y comentada en
[`Compiler/Parser/grammar_rules.py`](../Compiler/Parser/grammar_rules.py),
que la implementa 1:1. Resumen:

```ebnf
program         = { top_level_decl } ;
top_level_decl  = entity_decl | import_decl ;
import_decl     = "use" , identifier , { "." , identifier } , newline ;

entity_decl     = "entity" , identifier , [ "extends" , identifier ] ,
                   "{" , { entity_member } , "}" ;
entity_member   = property_decl | event_block | tag_decl ;
property_decl   = identifier , ":" , type_annotation , "=" , literal , newline ;
tag_decl        = "@" , identifier , [ "(" , arg_list , ")" ] , newline ;

event_block     = "on" , event_name , [ event_params ] , "{" , { statement } , "}" ;
event_name      = "touch" | "spawn" | "destroy" | "click"
                | "damage" | "interact" | "timer" ;

statement       = assignment | action_call | conditional | loop | emit_stmt ;
assignment      = identifier , ( "=" | "+=" | "-=" ) , expression , newline ;
action_call     = action_name , [ arg_list ] , newline ;
conditional     = "if" , expression , "{" , { statement } , "}" ,
                   [ "else" , "{" , { statement } , "}" ] ;
loop            = "repeat" , expression , "times" , "{" , { statement } , "}" ;
emit_stmt       = "emit" , identifier , [ arg_list ] , newline ;

comment         = line_comment | block_comment ;
line_comment    = "#" , { character - newline } , newline ;
block_comment   = "###" , { character } , "###" ;
```

## 4. Comparativa de eficiencia

Ver [`comparison.md`](./comparison.md) para el caso de uso completo del
"botón de puntuación" (28 líneas de Luau vs 7 líneas de ES).

## 5. Objetivos de v0.1

| Objetivo | Estado |
|---|---|
| Curva de aprendizaje < 1 hora | Ver esta guía completa: ~10 min de lectura |
| Reducción de verbosidad ≥ 70% | Validado en `Tests/transpiler_tests/` (ejemplo Coin: 75%) |
| Rendimiento equivalente a Luau escrito a mano | El Runtime es Luau puro optimizable independientemente |
| Compatibilidad total con Luau | Todo símbolo runtime usa prefijo `es_`, cero colisión de namespace |

## 6. Errores comunes

| Error | Causa típica |
|---|---|
| `EntityNameMustBePascalCase` | `entity coin { ... }` en vez de `entity Coin { ... }` |
| `UnknownEvent` | `on Touch(...)` en vez de `on touch(...)` (case-sensitive) |
| `ForbiddenAlias` | Usar `remove`/`delete`/`kill` en vez de `destroy` |
| `UndefinedProperty` | Asignar una variable que no es propiedad declarada ni parámetro de evento |
| `UnterminatedBlockComment` | Abrir `###` sin cerrarlo |
| `ModuleNotFound` | `use` apunta a un archivo `.es` que no existe |
| `CircularImport` | Dos o más archivos `.es` se importan entre sí formando un ciclo |
