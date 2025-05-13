from typing import List, Dict, Set, Optional
import os
import ast
from project_structure import ProjectStructure
from python_module import PythonModule
from import_visitor import ImportVisitor
from dependency import Dependency
import logging


class ProjectAnalyzer:
    """Анализирует структуру проекта и зависимости между модулями."""

    def __init__(
        self,
        project_root: str,
        project_structure: ProjectStructure,
        logger: logging.Logger,
    ) -> None:
        """
        Инициализирует анализатор проекта.

        Args:
            project_root: Корневая директория проекта
            project_structure: Структура проекта с определением кластеров
        """
        self.project_root = project_root
        self.project_structure = project_structure
        self.modules: Dict[str, PythonModule] = {}  # модули по путям
        self.module_by_name: Dict[str, PythonModule] = {}  # модули по именам
        self.dependencies: Set[Dependency] = set()
        self.logger = logger

    def find_python_files(self) -> List[str]:
        """Находит все Python файлы в проекте."""
        python_files = []
        for dirpath, dirnames, filenames in os.walk(self.project_root):
            # Пропускаем директории __pycache__ и другие скрытые директории
            dirnames[:] = [
                d for d in dirnames if not d.startswith("__") and not d.startswith(".")
            ]

            for filename in filenames:
                if filename.endswith(".py"):
                    python_files.append(os.path.join(dirpath, filename))

        self.logger.info(f"Найдено {len(python_files)} Python файлов")
        return python_files

    def normalize_path(self, path: str) -> str:
        """Нормализует путь относительно корня проекта."""
        rel_path = os.path.normpath(os.path.relpath(path, self.project_root))

        # Проверка на наличие вложенной структуры с дублированием имен пакетов
        parts = rel_path.split(os.sep)
        root_package = self.project_structure.root_package_name

        if len(parts) >= 2 and parts[0] == root_package and parts[1] == root_package:
            # Удаляем дублирующийся корневой пакет
            parts = parts[1:]
            rel_path = os.path.join(*parts)

        return rel_path

    def get_module_name(self, file_path: str) -> str:
        """Определяет имя модуля из пути к файлу."""
        rel_path = self.normalize_path(file_path)
        root_package = self.project_structure.root_package_name

        # Обработка для __init__.py
        if os.path.basename(file_path) == "__init__.py":
            parent_dir = os.path.dirname(rel_path)
            if parent_dir == ".":
                return root_package
            return parent_dir.replace(os.sep, ".")

        # Обработка обычных .py файлов
        module_path = os.path.splitext(rel_path)[0]
        return module_path.replace(os.sep, ".")

    def get_cluster_for_file(self, file_path: str) -> str:
        """Определяет кластер, к которому относится файл."""
        rel_path = self.normalize_path(file_path)
        root_package = self.project_structure.root_package_name

        for (
            path_prefix,
            cluster_name,
        ) in self.project_structure.cluster_mappings.items():
            if path_prefix == "":
                # Корневой кластер - файлы непосредственно в корневом пакете
                if rel_path == root_package or (
                    rel_path.startswith(f"{root_package}/")
                    and "/" not in rel_path[len(root_package) + 1 :]
                ):
                    return cluster_name
            elif (
                rel_path.startswith(f"{root_package}/{path_prefix}/")
                or rel_path == f"{root_package}/{path_prefix}"
            ):
                return cluster_name

        # По умолчанию - корневой кластер
        return "Root"

    def get_node_label(self, file_path: str, cluster: str) -> str:
        """Генерирует читаемую метку для узла."""
        rel_path = self.normalize_path(file_path)
        root_package = self.project_structure.root_package_name

        if cluster == "Root":
            return rel_path

        for (
            path_prefix,
            cluster_name,
        ) in self.project_structure.cluster_mappings.items():
            if cluster_name == cluster and path_prefix:
                prefix = f"{root_package}/{path_prefix}/"
                if rel_path.startswith(prefix):
                    return rel_path[len(prefix) :]

        return os.path.basename(file_path)

    def load_modules(self) -> None:
        """Загружает все модули проекта."""
        python_files = self.find_python_files()

        for file_path in python_files:
            module_name = self.get_module_name(file_path)
            cluster = self.get_cluster_for_file(file_path)
            module = PythonModule(
                file_path=file_path, module_name=module_name, cluster=cluster
            )

            self.modules[file_path] = module
            self.module_by_name[module_name] = module

        self.logger.info(f"Загружено {len(self.modules)} модулей")

    def analyze_imports(self) -> None:
        """Анализирует импорты во всех модулях проекта."""
        for module in self.modules.values():
            try:
                with open(module.file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content, module.file_path)
                visitor = ImportVisitor(module.module_name)
                visitor.visit(tree)

                module.imported_modules = visitor.imports

                # Создаем зависимости для модулей внутри проекта
                for imported_module_name, imported_objects in visitor.imports:
                    # Проверяем, импортируется ли модуль из нашего проекта
                    target_module = self.resolve_import(imported_module_name)
                    if target_module:
                        dependency = Dependency(
                            source_module=module,
                            target_module=target_module,
                            imported_objects=imported_objects,
                        )
                        self.dependencies.add(dependency)
            except SyntaxError:
                self.logger.warning(f"Не удалось разобрать файл: {module.file_path}")
            except Exception as e:
                self.logger.error(f"Ошибка при обработке {module.file_path}: {e}")

        self.logger.info(f"Обнаружено {len(self.dependencies)} зависимостей импортов")

    def resolve_import(self, imported_module_name: str) -> Optional[PythonModule]:
        """Разрешает имя импортированного модуля в объект модуля."""
        # Прямое соответствие
        if imported_module_name in self.module_by_name:
            return self.module_by_name[imported_module_name]

        # Поиск подмодулей или родительских модулей
        possible_modules = [
            name
            for name in self.module_by_name
            if name.startswith(f"{imported_module_name}.")
            or imported_module_name.startswith(f"{name}.")
        ]

        if possible_modules:
            # Берем наиболее конкретное соответствие
            best_match = max(possible_modules, key=len)
            return self.module_by_name[best_match]

        return None
