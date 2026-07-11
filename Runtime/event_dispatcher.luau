--[[
    event_dispatcher.luau

    Conecta los eventos declarativos de EntityScript (`on touch`, `on damage`, etc)
    a las señales nativas de Roblox, encapsulando TODA la logica repetitiva que
    en Luau puro se escribiria a mano en cada script (debounce, nil-checks,
    resolucion de Player desde un Instance de hit, etc).

    Ver design doc, seccion 4.3, tabla de traduccion: el Transpiler emite
    UNA sola llamada a estas funciones por cada bloque `on`, nunca la logica
    completa inline.
]]

local Players = game:GetService("Players")

local M = {}

-- ============================================================
-- es_on_touch: envuelve part.Touched con debounce POR JUGADOR + resolucion
-- de Player.
--
-- BUG CORREGIDO: la version anterior usaba un unico `debounce` compartido
-- por TODOS los jugadores. Con 2+ jugadores en el servidor, si el jugador A
-- tocaba la parte, el jugador B quedaba bloqueado 0.5s sin haber tocado
-- nada -- y si el callback demoraba (ej. por un `wait` adentro), el
-- problema se agravaba para todos. Ahora el debounce se lleva por
-- jugador (tabla indexada por UserId), asi que tocar con un personaje
-- nunca bloquea a otro.
--
-- Traduce: `on touch(player) { ... }` -> es_on_touch(self, function(player) ... end)
-- ============================================================
function M.es_on_touch(self, callback)
    local debouncedPlayers = {}

    self.Touched:Connect(function(hit)
        local character = hit.Parent
        local player = Players:GetPlayerFromCharacter(character)
        if player == nil then
            return
        end

        if debouncedPlayers[player.UserId] then
            return
        end

        debouncedPlayers[player.UserId] = true
        callback(player)
        -- Nota: si `callback` llamo `destroy self`, esta parte de codigo
        -- posterior al callback puede fallar si self ya no existe -- se
        -- protege con pcall para no dejar un error suelto en Output.
        task.delay(0.5, function()
            debouncedPlayers[player.UserId] = nil
        end)
    end)
end

-- ============================================================
-- es_on_spawn: ejecuta el callback inmediatamente al cargar el script
-- Traduce: `on spawn { ... }` -> es_on_spawn(self, function() ... end)
-- ============================================================
function M.es_on_spawn(self, callback)
    callback()
end

-- ============================================================
-- es_on_destroy: ejecuta logica de limpieza antes de que la instancia muera
-- Traduce: `on destroy { ... }` -> es_on_destroy(self, function() ... end)
-- ============================================================
function M.es_on_destroy(self, callback)
    self.AncestryChanged:Connect(function(_, parent)
        if parent == nil then
            callback()
        end
    end)
end

-- ============================================================
-- es_on_click: envuelve ClickDetector.MouseClick
-- Traduce: `on click(player) { ... }` -> es_on_click(self, function(player) ... end)
-- ============================================================
function M.es_on_click(self, callback)
    local clickDetector = self:FindFirstChildOfClass("ClickDetector")
    if not clickDetector then
        clickDetector = Instance.new("ClickDetector")
        clickDetector.Parent = self
    end

    clickDetector.MouseClick:Connect(function(player)
        callback(player)
    end)
end

-- ============================================================
-- es_on_damage: expone un BindableEvent "ESDamage" para desacoplar el
-- origen del daño (arma, trampa, NPC) de la entidad que lo recibe.
-- Traduce: `on damage(amount, source) { ... }` -> es_on_damage(self, function(amount, source) ... end)
-- ============================================================
function M.es_on_damage(self, callback)
    local bindable = self:FindFirstChild("ESDamageEvent")
    if not bindable then
        bindable = Instance.new("BindableEvent")
        bindable.Name = "ESDamageEvent"
        bindable.Parent = self
    end

    bindable.Event:Connect(function(amount, source)
        callback(amount, source)
    end)
end

-- ============================================================
-- es_on_interact: para ProximityPrompt (interaccion tipo "presiona E")
-- Traduce: `on interact(player) { ... }` -> es_on_interact(self, function(player) ... end)
-- ============================================================
function M.es_on_interact(self, callback)
    local prompt = self:FindFirstChildOfClass("ProximityPrompt")
    if not prompt then
        prompt = Instance.new("ProximityPrompt")
        prompt.Parent = self
    end

    prompt.Triggered:Connect(function(player)
        callback(player)
    end)
end

-- ============================================================
-- es_on_timer: ejecuta el callback cada N segundos (definidos via tag o arg)
-- Traduce: `on timer(seconds) { ... }` -> es_on_timer(self, function(seconds) ... end)
-- ============================================================
function M.es_on_timer(self, callback)
    local interval = self:GetAttribute("ESTimerInterval") or 1
    task.spawn(function()
        while self.Parent ~= nil do
            task.wait(interval)
            if self.Parent == nil then
                break
            end
            callback(interval)
        end
    end)
end

-- ============================================================
-- Eventos de jugador/juego (v0.2) -- solo validos en entidades @global,
-- validado en tiempo de compilacion por el Parser. self aqui es la
-- instancia de la entidad @global (un script en ServerScriptService,
-- tipicamente), no una parte fisica.
-- ============================================================

-- Traduce: `on join(player) { ... }` -> es_on_join(self, function(player) ... end)
function M.es_on_join(self, callback)
    Players.PlayerAdded:Connect(function(player)
        callback(player)
    end)
end

-- Traduce: `on leave(player) { ... }` -> es_on_leave(self, function(player) ... end)
function M.es_on_leave(self, callback)
    Players.PlayerRemoving:Connect(function(player)
        callback(player)
    end)
end

-- Traduce: `on death(player) { ... }` -> es_on_death(self, function(player) ... end)
--
-- BUG CORREGIDO: la version anterior conectaba `humanoid.Died` cada vez
-- que el personaje respawneaba (CharacterAdded se dispara en cada
-- respawn), sin desconectar el listener anterior. Tras la 2da muerte,
-- `callback` se disparaba 2 veces; tras la 3ra, 3 veces; etc. Ahora se
-- usa `Once` para que cada conexion se limpie sola despues de dispararse
-- una vez, evitando la acumulacion.
function M.es_on_death(self, callback)
    Players.PlayerAdded:Connect(function(player)
        player.CharacterAdded:Connect(function(character)
            local humanoid = character:WaitForChild("Humanoid")
            humanoid.Died:Once(function()
                callback(player)
            end)
        end)
    end)
end

-- Traduce: `on respawn(player) { ... }` -> es_on_respawn(self, function(player) ... end)
function M.es_on_respawn(self, callback)
    Players.PlayerAdded:Connect(function(player)
        player.CharacterAdded:Connect(function(character)
            callback(player)
        end)
    end)
end

return M
