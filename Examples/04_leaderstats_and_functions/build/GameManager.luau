--!strict
-- Generado automaticamente por EntityScript v0.2 -- NO EDITAR A MANO.
-- Fuente: Examples/04_leaderstats_and_functions/game.es

local es = require(game:GetService("ReplicatedStorage"):WaitForChild("EntityScriptRuntime"))
local es_give_stat = es.es_give_stat
local es_modify_score = es.es_modify_score
local es_set_score = es.es_set_score
local es_heal = es.es_heal
local es_apply_damage = es.es_apply_damage
local es_teleport = es.es_teleport
local es_message = es.es_message
local es_find = es.es_find
local es_play_sound = es.es_play_sound
local es_spawn = es.es_spawn
local es_wait = es.es_wait
local es_apply_tag = es.es_apply_tag
local es_inherit = es.es_inherit
local es_emit = es.es_emit
local es_on_touch = es.es_on_touch
local es_on_spawn = es.es_on_spawn
local es_on_destroy = es.es_on_destroy
local es_on_click = es.es_on_click
local es_on_damage = es.es_on_damage
local es_on_interact = es.es_on_interact
local es_on_timer = es.es_on_timer
local es_on_join = es.es_on_join
local es_on_leave = es.es_on_leave
local es_on_death = es.es_on_death
local es_on_respawn = es.es_on_respawn

local self = script.Parent

es_on_join(self, function(player)
    es_message(player, "Bienvenido al juego!")
end)

es_on_timer(self, function(seconds)
    for _, player in ipairs(game:GetService("Players"):GetPlayers()) do
        es_message(player, "Sigue jugando!")
    end
end)
