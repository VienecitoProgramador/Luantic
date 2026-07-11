"""
visitor.py
Implementacion del patron Visitor para recorrer el AST de EntityScript.

Por que Visitor y no metodos dentro de los nodos:
- Los nodos (nodes.py) deben permanecer como dataclasses puras, sin logica.
- Distintas fases del compilador (type_checker, comment_linter, luau_emitter)
  necesitan recorrer el MISMO AST con logica DISTINTA. Visitor permite anadir
  nuevas operaciones sobre el AST sin modificar nodes.py cada vez.

Cualquier componente nuevo (ej. un futuro "es_formatter" en v0.2) solo necesita
heredar de ASTVisitor e implementar los metodos visit_* que le interesen.
"""

from . import nodes as n


class ASTVisitor:
    """Clase base. Cada fase del compilador hereda de esta clase."""

    def visit(self, node):
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.generic_visit)
        return method(node)

    def generic_visit(self, node):
        raise NotImplementedError(
            f"No hay metodo visit_{type(node).__name__} implementado en {type(self).__name__}"
        )

    # ---- helpers para recorrer listas de sentencias ----

    def visit_block(self, statements: list):
        return [self.visit(stmt) for stmt in statements]
