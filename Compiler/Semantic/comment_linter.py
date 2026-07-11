"""
comment_linter.py
Chequeo NO BLOQUEANTE (warning, nunca error de compilacion) que detecta
comentarios probablemente redundantes: aquellos cuyo texto se parece
demasiado al nombre del statement/identifier que los sigue.

Justificacion (ver design doc, seccion "Clean Code" actualizada):
EntityScript permite comentarios, pero la filosofia sigue siendo que el
nombre de la entidad/evento/variable debe ser suficiente en la mayoria de
los casos. Este linter materializa esa filosofia como retroalimentacion
al desarrollador, sin ser paternalista (nunca bloquea el build).

Heuristica v0.1 (simple e intencionalmente conservadora):
- Se tokeniza el comentario en palabras significativas (>=3 letras).
- Se compara contra las palabras del identifier/action_name siguiente
  (separando snake_case/camelCase).
- Si la interseccion supera un umbral, se emite RedundantCommentWarning.

Esto es deliberadamente heuristico, no semantico: un linter de estilo no
debe intentar "entender" espanol/ingles de forma perfecta, solo dar una
senal util. Falsos negativos son preferibles a falsos positivos molestos.
"""

import re
from dataclasses import dataclass
from ..AST import nodes as n

_WORD_RE = re.compile(r"[a-zA-ZáéíóúÁÉÍÓÚñÑ]{3,}")


@dataclass
class CommentWarning:
    line: int
    comment_text: str
    reason: str

    def __str__(self):
        return f'Linea {self.line}: comentario probablemente redundante ("{self.comment_text}"). {self.reason}'


def _split_identifier_words(identifier: str) -> set[str]:
    # separa snake_case y camelCase en palabras individuales, en minuscula
    spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", identifier)
    spaced = spaced.replace("_", " ")
    return {w.lower() for w in _WORD_RE.findall(spaced)}


def _comment_words(text: str) -> set[str]:
    return {w.lower() for w in _WORD_RE.findall(text)}


def _is_redundant(comment_text: str, identifier: str, threshold: float = 0.6) -> bool:
    c_words = _comment_words(comment_text)
    i_words = _split_identifier_words(identifier)
    if not c_words or not i_words:
        return False
    overlap = c_words & i_words
    return (len(overlap) / max(len(i_words), 1)) >= threshold


class CommentLinter:
    """Recorre el AST buscando nodos con `leading_comment` y evalua redundancia."""

    def __init__(self):
        self.warnings: list[CommentWarning] = []

    def lint(self, program: n.Program) -> list[CommentWarning]:
        for entity in program.entities:
            self._check_node(entity, entity.name)
            for prop in entity.properties:
                self._check_node(prop, prop.name)
            for event in entity.events:
                self._check_node(event, event.event_name)
                self._lint_statements(event.body)
        return self.warnings

    def _lint_statements(self, statements: list[n.Stmt]):
        for stmt in statements:
            target = getattr(stmt, "target", None) or getattr(stmt, "action_name", None)
            if target:
                self._check_node(stmt, target)
            if isinstance(stmt, n.Conditional):
                self._lint_statements(stmt.then_branch)
                if stmt.else_branch:
                    self._lint_statements(stmt.else_branch)
            elif isinstance(stmt, n.Loop):
                self._lint_statements(stmt.body)

    def _check_node(self, node: n.Node, identifier: str):
        comment = getattr(node, "leading_comment", None)
        if comment and _is_redundant(comment, identifier):
            self.warnings.append(
                CommentWarning(
                    line=node.line,
                    comment_text=comment,
                    reason=(
                        'El comentario repite lo que ya expresa el nombre '
                        f'"{identifier}". Considera si aporta contexto de negocio '
                        'que el codigo no exprese, o eliminalo.'
                    ),
                )
            )


def lint_comments(program: n.Program) -> list[CommentWarning]:
    return CommentLinter().lint(program)
