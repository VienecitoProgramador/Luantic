"""
event_wrappers.py
Plantillas de codigo Luau para conectar eventos de EntityScript a las
señales nativas de Roblox, delegando la logica pesada al Runtime (es_stdlib).

Principio de arquitectura (ver design doc, seccion 4.3):
El transpiler NO genera logica de debounce/nil-checks inline en cada
entidad. Genera una LLAMADA CORTA a una funcion equivalente en
Runtime/event_dispatcher.luau. Esto garantiza:
  - Luau generado corto y legible.
  - Bugs de runtime se arreglan una vez en Runtime/, no en cada transpilacion.
  - Rendimiento identico al de un dispatcher escrito a mano.
"""

# Cada entrada mapea event_name (ES) -> nombre de funcion dispatcher en Runtime
EVENT_DISPATCHER_MAP = {
    "touch": "es_on_touch",
    "spawn": "es_on_spawn",
    "destroy": "es_on_destroy",
    "click": "es_on_click",
    "damage": "es_on_damage",
    "interact": "es_on_interact",
    "timer": "es_on_timer",
    "join": "es_on_join",
    "leave": "es_on_leave",
    "death": "es_on_death",
    "respawn": "es_on_respawn",
}


def wrap_event(event_name: str, params: list[str], body_code: str, indent: str = "    ") -> str:
    """
    Genera el bloque Luau que conecta un evento ES a su dispatcher runtime.

    Ejemplo de salida para `on touch(player) { ... }`:

        es_on_touch(self, function(player)
            <body_code>
        end)
    """
    dispatcher = EVENT_DISPATCHER_MAP[event_name]
    param_list = ", ".join(params)
    lines = [f"{dispatcher}(self, function({param_list})"]
    for line in body_code.splitlines():
        lines.append(f"{indent}{line}" if line.strip() else "")
    lines.append("end)")
    return "\n".join(lines)
