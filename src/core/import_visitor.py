import ast
import logging
from typing import List, Tuple


class ImportVisitor(ast.NodeVisitor):
    """AST visitor для извлечения импортов из Python файлов."""

    def __init__(self, module_name: str, logger: logging.Logger) -> None:
        """
        Инициализирует посетителя для анализа импортов.

        Args:
            module_name: Имя текущего модуля
        """
        self.module_name = module_name
        self.imports: List[Tuple[str, List[str]]] = []
        self.logger = logger

    def visit_Import(self, node: ast.Import) -> None:
        """Обрабатывает простые импорты вида 'import x'."""
        for name in node.names:
            self.imports.append((name.name, []))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Обрабатывает импорты вида 'from x import y'."""
        if node.module is None and node.level > 0:
            # Относительные импорты типа "from . import x"
            parts = self.module_name.split(".")
            if node.level <= len(parts):
                parent_module = ".".join(parts[: -node.level])
                for name in node.names:
                    if name.name == "*":
                        self.logger.warning(
                            f"Пропущен импорт со звездочкой в {self.module_name}"
                        )
                        continue
                    if parent_module:
                        full_module = f"{parent_module}.{name.name}"
                    else:
                        full_module = name.name
                    self.imports.append((full_module, []))
        elif node.level > 0:
            # Относительные импорты типа "from .x import y"
            parts = self.module_name.split(".")
            if node.level <= len(parts):
                parent_module = ".".join(parts[: -node.level])
                if parent_module and node.module:
                    full_module = f"{parent_module}.{node.module}"
                elif node.module:
                    full_module = node.module
                else:
                    full_module = parent_module

                imported_objects = [
                    name.name for name in node.names if name.name != "*"
                ]
                self.imports.append((full_module, imported_objects))
        else:
            # Абсолютные импорты типа "from x import y"
            imported_objects = [name.name for name in node.names if name.name != "*"]
            self.imports.append((node.module, imported_objects))

        self.generic_visit(node)
