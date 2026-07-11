# Ejemplo 02: Sistema de daño con herencia y módulos

Demuestra:
- `use Combat.Character` (import real entre archivos `.es`, resuelto por
  `Compiler/Semantic/module_resolver.py`)
- `entity ... extends ...` (herencia declarativa, ahora cruzando archivos)
- `on damage(amount, source)` con logica condicional
- `emit` para desacoplar la muerte del enemigo de quien escuche ese evento
  (ej. un sistema de logros, un contador de kills, etc.)
- El tag `@respawnable(15)` como metadata declarativa

Estructura:
```
02_damage_system/
├── Combat/
│   └── Character.es    <- entidad base, importada por enemy.es
└── enemy.es            <- usa `use Combat.Character`
```

Nota de diseño: `Goblin` hereda `health` de `Character` sin redeclararlo,
aunque `Character` vive en un archivo distinto. El `module_resolver.py`
fusiona ambos archivos en un solo `Program` antes de que el
`type_checker.py` valide la cadena de herencia, por lo que `extends`
funciona igual entre archivos que dentro del mismo archivo.
