--[[
    MessageDisplay.luau (LocalScript)

    Escucha el RemoteEvent "ESMessageEvent" (disparado por la accion
    `message` de EntityScript) y muestra el texto en pantalla.

    UBICACION: este script va en StarterPlayerScripts, como LocalScript
    (no como Script normal -- LocalScripts corren en el cliente, que es
    donde hace falta mostrar UI).

    Sin este script, `message player "..."` / `message all "..."` siguen
    funcionando del lado del servidor (no tiran error), pero el jugador
    NUNCA ve el texto, porque nada está escuchando el evento del lado
    del cliente. Este es el componente que falta para que "message" sea
    visible de verdad.

    Esta es una implementacion minima (un Label que aparece y desaparece).
    Se puede reemplazar por cualquier UI mas elaborada sin tocar el
    Runtime ni el Compiler -- el contrato es solo "escuchar ESMessageEvent
    y hacer algo visual con el texto".
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local player = Players.LocalPlayer

local messageEvent = ReplicatedStorage:WaitForChild("ESMessageEvent")

-- --- UI minima: un Label centrado arriba de la pantalla ---
local screenGui = Instance.new("ScreenGui")
screenGui.Name = "ESMessageDisplay"
screenGui.ResetOnSpawn = false
screenGui.Parent = player:WaitForChild("PlayerGui")

local label = Instance.new("TextLabel")
label.Size = UDim2.new(0.6, 0, 0.08, 0)
label.Position = UDim2.new(0.2, 0, 0.05, 0)
label.BackgroundColor3 = Color3.fromRGB(0, 0, 0)
label.BackgroundTransparency = 0.35
label.TextColor3 = Color3.fromRGB(255, 255, 255)
label.TextScaled = true
label.Font = Enum.Font.GothamBold
label.Text = ""
label.Visible = false
label.Parent = screenGui

local currentTween = nil

messageEvent.OnClientEvent:Connect(function(text)
    label.Text = tostring(text)
    label.Visible = true

    task.delay(3, function()
        -- Solo oculta si nadie mando un mensaje mas nuevo mientras esperaba
        if label.Text == tostring(text) then
            label.Visible = false
        end
    end)
end)
