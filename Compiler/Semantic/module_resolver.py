"""
module_resolver.py
Resuelve `import_decl` (`use Combat.DamageTypes`) a archivos .es reales en
disco y fusiona sus entidades en el Program principal ANTES del type-check.

Convencion de resolucion (v0.1, deliberadamente simple):
    `use Combat.DamageTypes` busca, relativo al directorio del archivo que
    hace el `use` y a cada `search_root` adicional dado:
        Combat/DamageTypes.es
        Combat.DamageTypes.es   (fallback plano)

Esto es intencionalmente parecido a como Python/Node resuelven modulos por
convencion de carpetas, para minimizar sorpresas en la curva de aprendizaje
(objetivo "< 1 hora", ver design doc).

Deteccion de ciclos: si A usa B y B usa A (directa o transitivamente), se
lanza CircularImportError con la cadena completa, en vez de recursion
infinita silenciosa.

Deduplicacion de "diamante" vs colision real de nombres:
    Si el MISMO archivo se importa desde dos caminos distintos (ej. A usa X,
    B usa X, y main usa A y B), sus entidades deben aparecer una sola vez:
    es el mismo archivo, no una colision.
    Si DOS ARCHIVOS DISTINTOS declaran una entidad con el MISMO NOMBRE (ej.
    a.es y b.es ambos definen `entity Coin`), eso es un error real del
    usuario -- silenciarlo (como hacia una version anterior de este modulo)
    podia descartar en silencio la entidad "equivocada" sin ningun aviso.
    Se rastrea de que archivo vino cada entidad para distinguir ambos casos.
"""

import os
from ..Lexer.tokenizer import tokenize_source
from ..Parser.grammar_rules import parse_tokens
from ..AST import nodes as n
from .module_errors import ModuleNotFoundError_, CircularImportError, DuplicateEntityAcrossModulesError


def _candidate_paths(import_path: list, base_dir: str, search_roots: list) -> list:
    rel_nested = os.path.join(*import_path) + ".es"
    rel_flat = ".".join(import_path) + ".es"
    candidates = []
    for root in [base_dir] + search_roots:
        candidates.append(os.path.join(root, rel_nested))
        candidates.append(os.path.join(root, rel_flat))
    return candidates


def _resolve_file(import_path: list, base_dir: str, search_roots: list, line: int) -> str:
    candidates = _candidate_paths(import_path, base_dir, search_roots)
    for path in candidates:
        if os.path.isfile(path):
            return os.path.abspath(path)
    raise ModuleNotFoundError_(".".join(import_path), candidates, line)


def resolve_program(
    program: n.Program,
    source_path: str,
    search_roots: list | None = None,
    _chain: list | None = None,
    _visited: dict | None = None,
    _origin_map: dict | None = None,
) -> n.Program:
    """
    Recorre program.imports, resuelve cada `use` a un archivo .es real,
    lo parsea recursivamente, y fusiona sus entidades ANTES de las del
    archivo actual (para que `extends` entre archivos funcione: la entidad
    padre debe existir en el Program combinado antes del type-check).

    _origin_map es un diccionario COMPARTIDO entre toda la recursion (nombre
    de entidad -> archivo absoluto donde fue DECLARADA originalmente, no el
    archivo del `use` intermedio que la trajo). Esto es lo que permite
    distinguir el caso "diamante" (A y B importan el mismo Shared.es, no es
    error) de una colision real (a.es y b.es declaran ambos `entity Coin`
    de forma independiente, que si es error).

    Retorna un nuevo Program con imports=[] (ya resueltos) y entities
    combinadas: [entidades importadas..., entidades propias...].
    """
    search_roots = search_roots or []
    chain = _chain or []
    visited = _visited if _visited is not None else {}
    origin_map = _origin_map if _origin_map is not None else {}

    base_dir = os.path.dirname(os.path.abspath(source_path))
    abs_source = os.path.abspath(source_path)

    if abs_source in chain:
        raise CircularImportError(abs_source, chain, line=1)

    if abs_source in visited:
        return visited[abs_source]

    # Registrar el origen real de las entidades propias de ESTE archivo,
    # antes de procesar imports (para que si algo mas las importa despues,
    # sepamos que "de verdad" vinieron de aca).
    for entity in program.entities:
        if entity.name not in origin_map:
            origin_map[entity.name] = abs_source
        elif origin_map[entity.name] != abs_source:
            raise DuplicateEntityAcrossModulesError(
                entity.name, origin_map[entity.name], abs_source, entity.line
            )

    for ls in program.leaderstats:
        origin_map.setdefault(f"__leaderstat__{ls.name}", abs_source)

    merged_entities: list[n.EntityDecl] = []
    merged_leaderstats: list[n.LeaderstatDecl] = []
    seen_names: set[str] = set()
    seen_leaderstat_names: set[str] = set()

    for imp in program.imports:
        imported_path = _resolve_file(imp.path, base_dir, search_roots, imp.line)

        with open(imported_path, "r", encoding="utf-8") as f:
            imported_source = f.read()

        tokens, comments = tokenize_source(imported_source, imported_path)
        imported_program = parse_tokens(tokens, comments)

        resolved_imported = resolve_program(
            imported_program,
            imported_path,
            search_roots,
            _chain=chain + [abs_source],
            _visited=visited,
            _origin_map=origin_map,
        )

        for entity in resolved_imported.entities:
            if entity.name in seen_names:
                continue  # ya lo trajo otro `use` en este mismo nivel (diamante local)
            merged_entities.append(entity)
            seen_names.add(entity.name)

        for ls in resolved_imported.leaderstats:
            if ls.name in seen_leaderstat_names:
                continue
            merged_leaderstats.append(ls)
            seen_leaderstat_names.add(ls.name)

    for entity in program.entities:
        if entity.name not in seen_names:
            merged_entities.append(entity)
            seen_names.add(entity.name)

    for ls in program.leaderstats:
        if ls.name not in seen_leaderstat_names:
            merged_leaderstats.append(ls)
            seen_leaderstat_names.add(ls.name)

    result = n.Program(imports=[], entities=merged_entities, leaderstats=merged_leaderstats, line=program.line)
    visited[abs_source] = result
    return result
