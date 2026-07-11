# Arquitectura del Proyecto

```
entityscript/
├── Compiler/
│   ├── Lexer/          tokenizer.py, token_types.py, lexer_errors.py
│   ├── Parser/         grammar_rules.py, syntax_errors.py
│   ├── AST/            nodes.py, visitor.py
│   ├── Semantic/       type_checker.py, symbol_table.py, comment_linter.py
│   └── Transpiler/     luau_emitter.py, templates/event_wrappers.py
├── Runtime/            es_stdlib.luau, event_dispatcher.luau, init.luau
├── Editor/             syntax_highlighting/, lsp/, snippets/
├── CLI/                es_build.py, es_watch.py, es_init.py
├── Examples/           01_coin/, 02_damage_system/, 03_npc_dialogue/
├── Docs/               este directorio
└── Tests/              lexer_tests/, parser_tests/, transpiler_tests/, integration_tests/
```

## Principio rector: separación estricta de responsabilidades

**`Compiler/` nunca importa de `Runtime/`.** El compilador genera *texto*
Luau que *llama* a funciones del Runtime; nunca ejecuta ni depende de ellas
directamente. Esto permite:

- Versionar el Runtime independientemente del Compiler (un fix en
  `es_give_stat` no requiere retranspiler ningún proyecto).
- A futuro, apuntar el mismo AST a otro backend sin tocar el Runtime.

## Pipeline de compilación

```
archivo.es
    │
    ▼
Lexer (tokenizer.py)
    │  produce: tokens (sin comentarios) + comment_table
    ▼
Parser (grammar_rules.py)
    │  produce: AST (Program)
    ▼
Semantic/type_checker.py
    │  produce: SymbolTable validada (o lanza SemanticError)
    ▼
Semantic/comment_linter.py
    │  produce: warnings no bloqueantes
    ▼
Transpiler/luau_emitter.py
    │  produce: {nombre_entidad: código_luau}
    ▼
CLI/es_build.py
    │  antepone el header con `require` del Runtime
    ▼
archivo(s) .luau en disco
```

Cada flecha es una función pura invocable independientemente — de ahí que
cada carpeta tenga su propia suite de tests en `Tests/`.

## Decisiones clave de módulo

### `Compiler/AST/` usa el patrón Visitor

Los nodos (`nodes.py`) son dataclasses puras sin lógica. Cada fase del
compilador (`type_checker`, `comment_linter`, `luau_emitter`) hereda de
`ASTVisitor` e implementa solo los métodos `visit_*` que necesita. Esto
permite añadir nuevas fases (ej. un futuro formateador `es_fmt` en v0.2)
sin modificar `nodes.py`.

### Propiedades se representan como Roblox Attributes, no `local`

Cada `property_decl` se traduce a `self:SetAttribute(...)` /
`self:GetAttribute(...)`, no a una variable Lua `local`. Esto es necesario
porque cada `entity` es un script Roblox independiente, y una propiedad
heredada de otra `entity` (ej. `health` en `Character` usado por `Goblin`)
no sería visible en el scope léxico de un script distinto. Los Attributes
viven en la instancia (`self`), no en el script, por lo que se comparten
naturalmente a través de la herencia declarada con `extends`.

Efecto colateral positivo: los Attributes son visibles y editables en vivo
desde el panel *Properties → Attributes* de Roblox Studio.

### Comentarios: capturados por el Lexer, filtrados antes del Parser

Ver `Compiler/Lexer/tokenizer.py`. El Lexer produce dos salidas: el stream
de tokens (sin comentarios, listo para el Parser) y una `comment_table`
lateral indexada por línea. El Parser asocia cada comentario al nodo AST
más cercano (`leading_comment`) para que `Editor/` y `Docs/` puedan
utilizarlo sin que contamine la lógica semántica del compilador.

### `Runtime/` es Luau puro, prefijado con `es_`

Todo símbolo público en `Runtime/es_stdlib.luau` y
`Runtime/event_dispatcher.luau` usa el prefijo `es_` (ej. `es_give_stat`,
`es_on_touch`) para garantizar cero colisión de namespace con Luau escrito
a mano en el mismo proyecto Roblox (objetivo "Total compatibilidad con
Luau").
