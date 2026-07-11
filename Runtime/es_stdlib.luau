--[[
    es_stdlib.luau

    Libreria estandar del Runtime de EntityScript.

    Este archivo es Luau puro, versionado independientemente del Compiler/.
    Es la UNICA parte del proyecto que un desarrollador Luau tradicional
    necesitaria leer o depurar directamente (ver design doc, seccion 3).

    Principio de diseño: el Transpiler genera llamadas CORTAS a estas
    funciones. Toda la complejidad (nil-checks, FindFirstChild anidado,
    gestion de instancias temporales) vive AQUI UNA SOLA VEZ, no se
    regenera en cada entidad transpilada.

    Convencion de naming: todo simbolo publico empieza con `es_` para
    garantizar cero colision de namespace con Luau/Roblox nativo
    (objetivo "Total compatibilidad con Luau").
]]

local Players = game:GetService("Players")

local M = {}

-- ============================================================
-- es_give_stat: da puntos/stats a un jugador via leaderstats
-- Traduce: `give player points` -> es_give_stat(self, player, points)
-- ============================================================
function M.es_give_stat(self, player, amount, statName)
    statName = statName or "Score"

    if player == nil then
        return false
    end

    local leaderstats = player:FindFirstChild("leaderstats")
    if not leaderstats then
        return false
    end

    local stat = leaderstats:FindFirstChild(statName)
    if not stat then
        return false
    end

    stat.Value = stat.Value + amount
    return true
end

-- ============================================================
-- es_play_sound: reproduce un sonido y lo limpia automaticamente
-- Traduce: `play sound` -> es_play_sound(self, soundId)
-- ============================================================
function M.es_play_sound(self, soundId)
    local sound = Instance.new("Sound")
    sound.SoundId = soundId
    sound.Parent = self

    sound:Play()
    sound.Ended:Connect(function()
        sound:Destroy()
    end)

    return sound
end

-- ============================================================
-- es_spawn: instancia una entidad (clona un modelo/template) en una posicion
-- Traduce: `spawn Enemy at position` -> es_spawn(self, "Enemy", position)
-- ============================================================
function M.es_spawn(self, entityName, position)
    local templates = game:GetService("ServerStorage"):FindFirstChild("EntityTemplates")
    if not templates then
        warn("[EntityScript] No se encontro ServerStorage.EntityTemplates")
        return nil
    end

    local template = templates:FindFirstChild(entityName)
    if not template then
        warn(("[EntityScript] Entidad '%s' no tiene template registrado"):format(entityName))
        return nil
    end

    local clone = template:Clone()
    if position and clone:IsA("Model") and clone.PrimaryPart then
        clone:SetPrimaryPartCFrame(CFrame.new(position))
    end
    clone.Parent = workspace
    return clone
end

-- ============================================================
-- es_wait: alias explicito sobre task.wait (evita usar wait() deprecado)
-- Traduce: `wait 2` -> es_wait(self, 2)
-- ============================================================
function M.es_wait(self, seconds)
    task.wait(seconds)
end

-- ============================================================
-- es_modify_score / es_set_score: modifican el leaderstat indicado por
-- `score = X` en la entidad que llama la accion (give/take/set en ES).
-- Traduce: `give player amount` -> es_modify_score(self, player, amount)
--          `take player amount` -> es_modify_score(self, player, -(amount))
--          `set player amount`  -> es_set_score(self, player, amount)
-- ============================================================
function M.es_modify_score(self, player, amount)
    local scoreTarget = self:GetAttribute("ESScoreTarget")
    if scoreTarget == nil then
        warn("[EntityScript] give/take usado sin 'score = X' declarado en la entidad")
        return false
    end
    return M.es_give_stat(self, player, amount, scoreTarget)
end

function M.es_set_score(self, player, amount)
    local scoreTarget = self:GetAttribute("ESScoreTarget")
    if scoreTarget == nil then
        warn("[EntityScript] set usado sin 'score = X' declarado en la entidad")
        return false
    end
    if player == nil then
        return false
    end
    local leaderstats = player:FindFirstChild("leaderstats")
    if not leaderstats then
        return false
    end
    local stat = leaderstats:FindFirstChild(scoreTarget)
    if not stat then
        return false
    end
    stat.Value = amount
    return true
end

-- ============================================================
-- es_heal / es_apply_damage: modifican la vida de un jugador o instancia.
--
-- Si el objetivo es un Player: usa Humanoid.Health REAL (la barra de vida
-- que Roblox muestra en pantalla), tomando su Character:FindFirstChild("Humanoid").
-- Si el objetivo es una Instance que no es Player (ej. una entidad Enemy
-- con `health = 100` declarado): usa el Attribute "health" que genera esa
-- property_decl.
--
-- BUG CORREGIDO: la version anterior asumia que TODO objetivo tenia un
-- Attribute "health", pero un Player real de Roblox nunca lo tiene seteado
-- salvo que el desarrollador lo haya puesto a mano -- por lo que
-- `heal player X` / `damage player X` fallaban siempre en silencio.
--
-- Traduce: `heal player 20` -> es_heal(player, 20)
--          `damage player 15` -> es_apply_damage(player, 15)
-- NOTA: `damage` (accion) y `on damage` (evento) son independientes;
-- llamar a la accion NO dispara el evento automaticamente.
-- ============================================================
local function _resolveHumanoid(target)
    if typeof(target) ~= "Instance" then
        return nil
    end
    if target:IsA("Player") then
        local character = target.Character
        if not character then
            return nil
        end
        return character:FindFirstChildOfClass("Humanoid")
    end
    if target:IsA("Model") then
        return target:FindFirstChildOfClass("Humanoid")
    end
    return nil
end

function M.es_heal(target, amount)
    if target == nil then
        return false
    end

    local humanoid = _resolveHumanoid(target)
    if humanoid then
        humanoid.Health = math.min(humanoid.Health + amount, humanoid.MaxHealth)
        return true
    end

    -- Fallback: instancia sin Humanoid (ej. una entidad ES con `health = N`
    -- declarado como Attribute, como un Enemy).
    local current = target:GetAttribute("health")
    if current == nil then
        warn("[EntityScript] heal: el objetivo no tiene Humanoid ni atributo 'health'")
        return false
    end
    target:SetAttribute("health", current + amount)
    return true
end

function M.es_apply_damage(target, amount)
    if target == nil then
        return false
    end

    local humanoid = _resolveHumanoid(target)
    if humanoid then
        humanoid:TakeDamage(amount)
        return true
    end

    local current = target:GetAttribute("health")
    if current == nil then
        warn("[EntityScript] damage: el objetivo no tiene Humanoid ni atributo 'health'")
        return false
    end
    target:SetAttribute("health", current - amount)
    return true
end

-- ============================================================
-- es_teleport: mueve al jugador (o su character) a una posicion o
-- instancia con nombre dado (busca en workspace por nombre).
-- Traduce: `teleport player Spawn` -> es_teleport(player, Spawn)
-- ============================================================
function M.es_teleport(target, destination)
    if target == nil or destination == nil then
        return false
    end

    local character = target
    if target:IsA("Player") then
        -- El personaje puede no haber cargado todavia (ej. justo al hacer
        -- join). Se espera un tiempo corto antes de rendirse, en vez de
        -- fallar en silencio como antes.
        character = target.Character or target:WaitForChild("Character", 5)
    end
    if not character then
        warn("[EntityScript] teleport: el jugador no tiene Character cargado")
        return false
    end

    local rootPart = character:FindFirstChild("HumanoidRootPart") or character:WaitForChild("HumanoidRootPart", 5)
    if not rootPart then
        return false
    end

    local destPosition
    if typeof(destination) == "Vector3" then
        destPosition = destination
    elseif typeof(destination) == "Instance" then
        destPosition = destination.Position or (destination.PrimaryPart and destination.PrimaryPart.Position)
    elseif typeof(destination) == "string" then
        local found = workspace:FindFirstChild(destination)
        if found then
            destPosition = found.Position or (found.PrimaryPart and found.PrimaryPart.Position)
        end
    end

    if not destPosition then
        warn("[EntityScript] teleport: no se pudo resolver el destino")
        return false
    end

    rootPart.CFrame = CFrame.new(destPosition)
    return true
end

-- ============================================================
-- es_message: envia un mensaje a un jugador, a todos, o a un equipo.
-- Traduce: `message player "Hola"`      -> es_message(player, "Hola")
--          `message all "Hola"`         -> es_message("all", "Hola")
--          `message team Red "Hola"`    -> es_message("team:Red", "Hola")
--
-- BUG CORREGIDO (importante): la version anterior usaba un BindableEvent,
-- pero BindableEvent NO cruza el limite cliente-servidor en Roblox -- solo
-- sirve para comunicar scripts que corren en el MISMO lado (servidor con
-- servidor, o cliente con cliente). Como `message` se ejecuta en el
-- servidor pero el jugador necesita VER el texto en su pantalla (cliente),
-- hace falta un RemoteEvent, que es el unico tipo de instancia pensado
-- para cruzar esa frontera.
--
-- Se crea (si no existe) un RemoteEvent "ESMessageEvent" en
-- ReplicatedStorage. Para que el mensaje se vea en pantalla, hace falta
-- un LocalScript en StarterPlayerScripts que lo escuche -- ver el ejemplo
-- minimo en Docs/language_spec.md, seccion "Mostrar mensajes en pantalla".
-- ============================================================
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local _messageEvent = ReplicatedStorage:FindFirstChild("ESMessageEvent")
if not _messageEvent then
    _messageEvent = Instance.new("RemoteEvent")
    _messageEvent.Name = "ESMessageEvent"
    _messageEvent.Parent = ReplicatedStorage
end

function M.es_message(target, text)
    if typeof(target) == "Instance" and target:IsA("Player") then
        _messageEvent:FireClient(target, text)
    elseif target == "all" then
        _messageEvent:FireAllClients(text)
    elseif typeof(target) == "string" and target:sub(1, 5) == "team:" then
        local teamName = target:sub(6)
        local team = game:GetService("Teams"):FindFirstChild(teamName)
        if team then
            for _, player in ipairs(team:GetPlayers()) do
                _messageEvent:FireClient(player, text)
            end
        end
    end
end

-- ============================================================
-- es_find: busca todas las instancias vivas de una entidad por nombre
-- (asume que el nombre de la Instance coincide con el nombre de la
-- entidad ES, convencion usada tambien por es_spawn).
-- Traduce: `find Coin` -> es_find("Coin")
-- ============================================================
function M.es_find(entityName)
    local results = {}
    for _, obj in ipairs(workspace:GetDescendants()) do
        if obj.Name == entityName then
            table.insert(results, obj)
        end
    end
    return results
end

-- ============================================================
-- es_apply_tag: aplica comportamiento de un tag declarativo (@locked, etc)
-- Traduce: `@locked` -> es_apply_tag(self, "locked")
-- ============================================================
function M.es_apply_tag(self, tagName, ...)
    if tagName == "locked" then
        self:SetAttribute("ESLocked", true)
    elseif tagName == "respawnable" then
        local seconds = ...
        self:SetAttribute("ESRespawnSeconds", seconds or 10)
    elseif tagName == "serveronly" then
        if not game:GetService("RunService"):IsServer() then
            self:Destroy()
        end
    elseif tagName == "clientonly" then
        if not game:GetService("RunService"):IsClient() then
            self:Destroy()
        end
    else
        warn(("[EntityScript] Tag desconocido: @%s"):format(tagName))
    end
end

-- ============================================================
-- es_inherit: copia atributos/comportamiento de una entidad padre
-- Traduce: `entity Enemy extends Character` -> es_inherit(self, "Character")
-- ============================================================
function M.es_inherit(self, parentEntityName)
    self:SetAttribute("ESParentEntity", parentEntityName)
end

-- ============================================================
-- es_emit: emite un evento custom entre entidades via BindableEvent
-- Traduce: `emit ScoreChanged(points)` -> es_emit("ScoreChanged", self, points)
-- ============================================================
local _bindables = {}

function M.es_emit(eventName, self, ...)
    local bindable = _bindables[eventName]
    if bindable then
        bindable:Fire(self, ...)
    end
end

function M.es_get_bindable(eventName)
    if not _bindables[eventName] then
        _bindables[eventName] = Instance.new("BindableEvent")
    end
    return _bindables[eventName]
end

return M
