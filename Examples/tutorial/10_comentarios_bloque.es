###
EJEMPLO 10: Comentarios de bloque (para textos largos)

Hasta ahora usamos comentarios de una linea con el simbolo numeral.
Cuando necesitas escribir varias lineas seguidas (por ejemplo, para
explicar una decision de diseno larga), podes abrir un comentario de
bloque con tres numerales seguidos, escribir todo lo que necesites en
varias lineas, y cerrarlo repitiendo esos mismos tres numerales al
final.

Regla de estilo: usa comentarios para explicar el "por que" de una
decision, no el "que" hace el codigo (eso ya lo dice el nombre de las
variables y acciones).
###

entity NPCVendor {
    # Nombre elegido por el equipo de diseno narrativo, no cambiar sin avisar
    name = "Grimlock el Comerciante"
}
