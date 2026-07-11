# Luantic (EntityScript) v0.2

> ⚠️ **Aviso:** este es un mini proyecto hecho por diversión y como testeo
> de desarrollo de código. Está en una etapa **muy inestable** — no es un
> producto terminado ni pensado para producción. Usalo, rompelo, y si
> querés, arreglalo vos mismo.

**Luantic** es el editor de escritorio de **EntityScript**, un DSL
orientado a entidades y eventos que transpila a Luau real.

```
entity Coin {
    points: Number = 10

    on touch(player) {
        give player points
        destroy self
    }
}
```

...se compila a Luau real (ver `Examples/01_coin/build/Coin.luau`).

## Open source — hacé lo que quieras con esto

Este proyecto es **100% open source**. Cualquiera puede:

- Usar el compilador y el editor libremente.
- Modificar la interfaz de Luantic, o rehacerla por completo.
- Publicar sus propias versiones/forks de Luantic sin pedir permiso.
- Contribuir con cambios al compilador, al lenguaje o al editor.

El código fuente completo está en este repositorio:

**Repositorio:** *(agregar link acá)*

## Requisitos

- Python 3.10+ (usa sintaxis `X | Y` de tipos y `match`-free pero necesita 3.10+)
- Sin dependencias externas para el compilador (solo librería estándar)
- `pytest` opcional, solo para correr la suite de tests
- Para el editor de escritorio: `tkinter` (incluido por defecto en Windows/Mac;
  en Linux puede requerir `sudo apt install python3-tk`)

## Probarlo en 30 segundos

```bash
cd entityscript

# Compilar el ejemplo mas simple
python3 CLI/es_build.py Examples/01_coin/coin.es --out /tmp/salida

cat /tmp/salida/Coin.luau
```

Deberías ver el Luau generado con debounce, resolución de Player y
gestión de Sound ya resueltas por el Runtime — sin que tuvieras que
escribir nada de eso.

## Correr la suite de tests

```bash
pip install pytest --break-system-packages   # si no lo tenés instalado
python3 -m pytest Tests/ -v
```

Deberías ver 44 tests en verde.

## Crear un proyecto nuevo

```bash
python3 CLI/es_init.py mi_juego
python3 CLI/es_build.py mi_juego/src/main.es --out mi_juego/build
```

## Ver cambios en vivo mientras editás

```bash
python3 CLI/es_watch.py Examples/01_coin/coin.es --out /tmp/salida
```

## ¿Recién arrancás? Empezá por acá

`Examples/tutorial/` tiene **50 ejemplos numerados**, cada uno enseñando
un concepto nuevo del lenguaje, del más simple al más avanzado. Todos
compilan de verdad y tienen comentarios explicando qué hacen y por qué.
Es la forma más rápida de aprender EntityScript sin leer toda la
documentación de una sentada — ver `Examples/tutorial/README.md` para
el índice completo.

```bash
python3 CLI/es_build.py Examples/tutorial/05_moneda_clasica.es --out /tmp/salida
```

O simplemente abrí cualquiera de esos archivos desde Luantic
(**Archivo → Abrir .es...**) y mirá el Luau que genera.

## Ejemplos "showcase" (proyectos más completos)

| Ejemplo | Qué demuestra |
|---|---|
| `Examples/01_coin/` | Caso base: entidad + evento + acciones |
| `Examples/02_damage_system/` | Herencia (`extends`) + **imports reales entre archivos** (`use`) |
| `Examples/03_npc_dialogue/` | Comentarios de bloque, loops (`repeat`), interacción con `ProximityPrompt` |
| `Examples/04_leaderstats_and_functions/` | Leaderstats, `score`, `const`, `function`, entidades `@global` |

Cada carpeta de ejemplo trae su propio `README.md` explicando qué mirar.

## Luantic — editor de escritorio (recomendado)

**Luantic** es una app de escritorio real (ventana nativa, sin navegador)
hecha con Tkinter — viene incluido con Python, no hay que instalar nada
más en Windows/Mac.

**Windows:** doble clic en `abrir_editor.bat`
**Mac/Linux:** doble clic en `abrir_editor.sh` (o `./abrir_editor.sh` desde terminal)

O directamente:

```bash
python3 Editor/desktop_app.py
```

Se abre una ventana con el código a la izquierda y el Luau generado a la
derecha. Autocompila mientras escribís, marca errores con línea exacta,
y tiene menú **Archivo** para abrir/guardar `.es` y exportar el resultado
a un `.zip` con todos los `.luau` listos para pegar en Roblox Studio.

Algunos detalles de Luantic:

- **Autocompilación en vivo** mientras escribís (podés desactivarla en
  **Ver → Autocompilar**).
- **Resaltado de sintaxis** propio para EntityScript.
- **Pantalla completa real**: `F11` para activarla, `Esc` para salir.
- Atajos: `Ctrl+N` nuevo, `Ctrl+O` abrir, `Ctrl+S` guardar, `Ctrl+E`
  exportar `.zip`, `Ctrl+Enter` compilar, `Ctrl+J` mostrar/ocultar salida
  (en Mac, `Cmd` en vez de `Ctrl`).

Al igual que el editor web, **Luantic no reimplementa el compilador** —
llama directo a `Compiler/`, la única implementación real.

## Editor web (alternativa)

Si preferís usar el navegador en vez de una ventana nativa:

```bash
python3 Editor/webapp/server.py
```

Esto abre automáticamente `http://localhost:8765`. Mismo principio: la
interfaz solo le habla al mismo `Compiler/` de Python vía un servidor local.
Presionás "▶ Compilar" (o `Ctrl+Enter`), y ves el Luau generado a la
derecha — con errores de compilación reales, mismo pipeline que usa
`es_build.py`.

## Estructura del proyecto

```
Compiler/     Lexer -> Parser -> AST -> Semantic -> Transpiler (todo Python puro, UNICA implementacion)
Runtime/      La libreria Luau que el codigo generado importa (es_stdlib, event_dispatcher)
CLI/          es_build (compilar), es_watch (recompilar en vivo), es_init (scaffolding)
Editor/desktop_app.py  Luantic: app de escritorio (Tkinter) que llama al mismo Compiler/, sin duplicarlo
Editor/webapp/         Alternativa: servidor local + interfaz HTML/JS, mismo principio
Examples/     4 proyectos de ejemplo, ya compilados en sus carpetas build/
Docs/         Especificación del lenguaje, arquitectura, filosofía de diseño
Tests/        83 tests con pytest (lexer, parser, semántica, transpiler, imports, features v0.2, tutorial)
```

Ver `Docs/language_spec.md` para la sintaxis completa y `Docs/architecture.md`
para el diseño interno del compilador.

## Qué es esto (honestidad de prototipo)

Es un compilador real que funciona de punta a punta: tokeniza, parsea,
valida tipos/herencia, resuelve imports entre archivos, y genera Luau
sintácticamente correcto. **No** tiene: LSP con interfaz, resolución
de funciones reutilizables entre entidades (`define behavior`, planeado
para una futura versión), ni ha sido probado dentro de Roblox Studio real
(el Luau generado sigue las APIs correctas de Roblox pero no se ejecutó
en el motor).

Como se aclara arriba, **este es un proyecto inestable, hecho por
diversión y como testeo** — no hay garantías de estabilidad ni de
mantenimiento continuo. Si algo no compila como esperás, correr con
`python3 CLI/es_build.py archivo.es` te va a dar un error con línea y
explicación — ese es el comportamiento esperado, no un bug silencioso.

## Créditos

Creado por **Vienestor**.

TikTok: [@vienestorstudio](https://www.tiktok.com/@vienestorstudio)

Como el proyecto es open source, si hacés tu propia versión o fork de
Luantic, no hace falta pedir permiso — solo compartilo si querés que
otros lo vean.
