-- Generado automaticamente por EntityScript v0.2 -- Leaderstats
-- Colocar este script en ServerScriptService.

local Players = game:GetService("Players")

Players.PlayerAdded:Connect(function(player)
    local leaderstats = Instance.new("Folder")
    leaderstats.Name = "leaderstats"
    leaderstats.Parent = player

    local Coins = Instance.new("IntValue")
    Coins.Name = "Coins"
    Coins.Value = 0
    Coins.Parent = leaderstats

    local Wins = Instance.new("IntValue")
    Wins.Name = "Wins"
    Wins.Value = 0
    Wins.Parent = leaderstats

end)