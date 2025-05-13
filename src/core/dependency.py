from dataclasses import dataclass, field
from .python_module import PythonModule
from typing import List


@dataclass
class Dependency:
    """Представляет зависимость между двумя модулями."""

    source_module: PythonModule  # Исходный модуль (импортирующий)
    target_module: PythonModule  # Целевой модуль (импортируемый)
    imported_objects: List[str] = field(default_factory=list)  # Импортированные объекты

    def __hash__(self):
        return hash((self.source_module.file_path, self.target_module.file_path))
