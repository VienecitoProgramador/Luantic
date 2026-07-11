--[[
    init.luau

    Punto de entrada unico del Runtime de EntityScript.
    Este es el modulo que el codigo transpilado importa via:

        local es = require(ReplicatedStorage.EntityScriptRuntime)

    Combina es_stdlib.luau (acciones) y event_dispatcher.luau (eventos)
    en una sola tabla plana, y ademas "derrama" cada funcion como global
    de script para que el codigo generado por el Transpiler pueda llamar
    `es_give_stat(...)` directamente sin prefijo de tabla (mantiene el
    Luau generado mas corto y legible, ver design doc seccion 4.3).

    Este archivo debe colocarse en ReplicatedStorage como ModuleScript
    llamado "EntityScriptRuntime" (o ajustar el path segun convencion
    del estudio).
]]

local stdlib = require(script.Parent.es_stdlib)
local dispatcher = require(script.Parent.event_dispatcher)

local Runtime = {}

for name, fn in pairs(stdlib) do
    Runtime[name] = fn
end

for name, fn in pairs(dispatcher) do
    Runtime[name] = fn
end

--[[
    NOTA DE ARQUITECTURA sobre "compatibilidad total con Luau":

    El codigo generado por el Transpiler llama a funciones como
    `es_give_stat(...)` como si fueran globales del script, no como
    `es.es_give_stat(...)`. Para lograrlo sin ensuciar _G real de Roblox
    (lo cual violaria total_compatibilidad_con_luau), la plantilla base
    que el CLI antepone a cada script generado (ver CLI/es_build) inyecta
    un bloque de `local es_give_stat = es.es_give_stat` por cada funcion
    usada, resuelto en tiempo de compilacion (no en runtime). Este modulo
    solo expone la tabla; el "aplanado" ocurre en el codigo generado.
]]

return Runtime
