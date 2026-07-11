# EJEMPLO 36: Tag "@locked" (marcar un objeto como bloqueado)
#
# "@locked" es un tag que marca la entidad como bloqueada, para que
# otros sistemas del juego (o tu propio codigo Luau adicional) puedan
# revisar ese estado y decidir que hacer. Por si solo no impide nada
# automaticamente: es una etiqueta que vos despues consultas.

entity TreasureVault {
    @locked
}
