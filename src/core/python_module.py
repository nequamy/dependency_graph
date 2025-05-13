from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class PythonModule:
    """Представляет Python модуль с его путем и именем."""

    file_path: str  # Путь к файлу
    module_name: str  # Полное имя модуля
    cluster: Optional[str] = None  # Кластер, к которому относится модуль
    imported_modules: List[Tuple[str, List[str]]] = field(
        default_factory=list
    )  # Импортированные модули

    def __hash__(self):
        return hash(self.file_path)
