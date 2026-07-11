# EJEMPLO 48: "use" (reutilizar codigo de OTRO archivo .es)
#
# Cuando un proyecto crece, conviene separar el codigo en varios
# archivos en vez de tener todo en uno solo gigante. "use" trae las
# entidades declaradas en otro archivo para poder usarlas aca, incluso
# para "extends" (herencia entre archivos distintos).
#
# Este ejemplo importa "Character" desde Shared/Character.es (mira esa
# carpeta al lado de este archivo) y lo usa como base para un Orc.
#
# "use Shared.Character" busca el archivo Shared/Character.es, tomando
# el punto como separador de carpetas.

use Shared.Character

entity Orc extends Character {
    on damage(amount, source) {
        health -= amount
    }
}
