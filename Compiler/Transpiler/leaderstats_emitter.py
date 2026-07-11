"""
leaderstats_emitter.py
Genera el script Luau que crea el Folder "leaderstats" y sus IntValue
para cada `leaderstat X = N` declarado a nivel de Program.

Este script es independiente de las entidades: va en ServerScriptService,
no en una parte especifica, ya que gestiona el ciclo de vida de TODOS
los jugadores que entren al juego (PlayerAdded).
"""

from ..AST import nodes as n


def _format_number(value: float) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def emit_leaderstats_script(leaderstats: list[n.LeaderstatDecl]) -> str | None:
    """
    Retorna None si no hay ningun `leaderstat` declarado (no genera archivo
    vacio innecesario). Si hay al menos uno, retorna el script completo.
    """
    if not leaderstats:
        return None

    lines = [
        "-- Generado automaticamente por EntityScript v0.2 -- Leaderstats",
        "-- Colocar este script en ServerScriptService.",
        "",
        'local Players = game:GetService("Players")',
        "",
        "Players.PlayerAdded:Connect(function(player)",
        '    local leaderstats = Instance.new("Folder")',
        '    leaderstats.Name = "leaderstats"',
        "    leaderstats.Parent = player",
        "",
    ]

    for ls in leaderstats:
        lines.append(f'    local {ls.name} = Instance.new("IntValue")')
        lines.append(f'    {ls.name}.Name = "{ls.name}"')
        lines.append(f'    {ls.name}.Value = {_format_number(ls.initial)}')
        lines.append(f'    {ls.name}.Parent = leaderstats')
        lines.append("")

    lines.append("end)")
    return "\n".join(lines)
