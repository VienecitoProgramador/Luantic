# Filosofía de Diseño y Comparativa de Eficiencia

## 1. Principios

### "Una única forma de hacer las cosas"
No existen sinónimos para acciones reservadas. `destroy` es la única forma
de eliminar una instancia; `remove`, `delete`, `kill` disparan
`ForbiddenAliasError` en el Lexer (ver `Compiler/Lexer/tokenizer.py`,
`FORBIDDEN_ACTION_ALIASES`).

### "Zero Boilerplate"
No existe `local`, no existe `end` (los bloques cierran con `}`), no existe
gestión manual de `:Connect()`. El transpiler infiere todo eso.

### "Clean Code" (comentarios permitidos, no obligatorios)
Los comentarios existen (`#` línea, `###` bloque) pero se recomiendan
solo cuando documentan contexto de negocio que el código no puede expresar.
El `comment_linter.py` emite warnings no bloqueantes ante comentarios
redundantes.

## 2. Comparativa: botón de puntuación

### Luau estándar (verboso, ~28 líneas)

```lua
local part = script.Parent
local debounce = false
local points = 10

local function onTouch(hit)
    if debounce then return end
    local character = hit.Parent
    local player = game.Players:GetPlayerFromCharacter(character)
    if player == nil then return end
    debounce = true

    local leaderstats = player:FindFirstChild("leaderstats")
    if leaderstats then
        local score = leaderstats:FindFirstChild("Score")
        if score then
            score.Value = score.Value + points
        end
    end

    local sound = Instance.new("Sound")
    sound.SoundId = "rbxassetid://1234567"
    sound.Parent = part
    sound:Play()

    part:Destroy()
end

part.Touched:Connect(onTouch)
```

### EntityScript (7 líneas, -75%)

```
entity Coin {
    points: Number = 10
    sound: Sound = "rbxassetid://1234567"

    on touch(player) {
        give player points
        play sound
        destroy self
    }
}
```

### Luau generado por el transpiler (real, ejecutar `Examples/01_coin`)

```lua
local self = script.Parent

self:SetAttribute("points", 10)
self:SetAttribute("sound", "rbxassetid://1234567")

es_on_touch(self, function(player)
    es_give_stat(self, player, self:GetAttribute("points"))
    es_play_sound(self, self:GetAttribute("sound"))
    self:Destroy()
end)
```

El debounce, la resolución de `Player` desde `hit`, y el `FindFirstChild`
anidado viven **una sola vez** en `Runtime/event_dispatcher.luau` y
`Runtime/es_stdlib.luau`, reutilizados por cualquier entidad.

## 3. Roadmap

- **v0.1** (actual): entidades, eventos base, transpiler funcional, CLI,
  sin funciones reutilizables entre entidades.
- **v0.2**: `define behavior` para lógica compartida, imports reales entre
  archivos `.es`, LSP básico.
- **v0.3**: namespaces de entidades, modo `strict` opcional, generación
  automática de documentación desde `comment_table` + estructura de AST.
