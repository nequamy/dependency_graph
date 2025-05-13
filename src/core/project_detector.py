from .project_structure import ProjectStructure
import os
import sys
from typing import Optional
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class ProjectDetector:
    """Определяет корневую директорию проекта и его структуру."""

    @staticmethod
    def detect_project_structure(project_root: str) -> ProjectStructure:
        """
        Автоматически определяет структуру проекта.

        Args:
            project_root: Корневая директория проекта

        Returns:
            Структура проекта с определенными кластерами
        """
        # Определение корневого пакета
        root_package = None
        possible_root_packages = []

        # Проверяем все поддиректории на наличие __init__.py
        for item in os.listdir(project_root):
            item_path = os.path.join(project_root, item)
            if os.path.isdir(item_path) and os.path.exists(
                os.path.join(item_path, "__init__.py")
            ):
                possible_root_packages.append(item)

        # Если есть только один пакет в корне, скорее всего это наш корневой пакет
        if len(possible_root_packages) == 1:
            root_package = possible_root_packages[0]
        # Если есть несколько, ищем наиболее вероятный по числу Python файлов
        elif len(possible_root_packages) > 1:
            max_files = 0
            for pkg in possible_root_packages:
                pkg_path = os.path.join(project_root, pkg)
                py_files_count = sum(
                    1 for f in os.listdir(pkg_path) if f.endswith(".py")
                )
                if py_files_count > max_files:
                    max_files = py_files_count
                    root_package = pkg

        # Если не нашли пакеты, используем имя директории проекта
        if not root_package:
            root_package = os.path.basename(project_root)

        # Автоматическое определение структуры кластеров
        cluster_mappings = {"": "Root"}  # По умолчанию все в корневом кластере

        # Если имеется корневой пакет, проверяем его структуру
        if os.path.exists(os.path.join(project_root, root_package)):
            root_package_path = os.path.join(project_root, root_package)

            # Определяем поддиректории, которые являются пакетами (содержат __init__.py)
            for item in os.listdir(root_package_path):
                item_path = os.path.join(root_package_path, item)

                # Если это папка, начинается с подчеркивания и содержит __init__.py
                if os.path.isdir(item_path) and os.path.exists(
                    os.path.join(item_path, "__init__.py")
                ):
                    if item.startswith("_"):
                        # Считаем такие папки основными компонентами
                        component_name = item[1:].capitalize()
                        cluster_mappings[item] = component_name
                    elif item == "services" or item == "_services":
                        # Для сервисов проверяем подпапки
                        services_path = item_path
                        for service in os.listdir(services_path):
                            service_path = os.path.join(services_path, service)
                            if os.path.isdir(service_path) and os.path.exists(
                                os.path.join(service_path, "__init__.py")
                            ):
                                # Добавляем каждый сервис как отдельный кластер
                                service_prefix = f"{item}/{service}"
                                cluster_mappings[service_prefix] = service.upper()

        # Создаем и возвращаем структуру проекта
        return ProjectStructure(root_package, cluster_mappings)

    @staticmethod
    def find_project_root(specified_path: Optional[str] = None) -> str:
        """
        Автоматически определяет корневую директорию проекта.

        Args:
            specified_path: Опционально указанный путь к проекту

        Returns:
            Путь к обнаруженной корневой директории проекта
        """
        if specified_path:
            abs_path = os.path.abspath(specified_path)
            if os.path.exists(abs_path):
                return abs_path
            else:
                logger.error(f"Указанная директория проекта не существует: {abs_path}")
                sys.exit(1)

        # Начинаем с текущей директории
        current_dir = os.path.abspath(".")

        # Определяем возможные маркеры проекта
        project_markers = [
            "setup.py",
            "pyproject.toml",
            "requirements.txt",
            ".git",
            "src",
        ]

        # Проверка текущей директории
        project_markers_found = sum(
            1
            for marker in project_markers
            if os.path.exists(os.path.join(current_dir, marker))
        )
        if project_markers_found >= 1:
            logger.info(f"Корень проекта обнаружен в текущей директории: {current_dir}")
            return current_dir

        # Проверка родительских директорий
        max_levels_up = 4
        dir_to_check = current_dir

        for _ in range(max_levels_up):
            parent_dir = os.path.dirname(dir_to_check)
            if parent_dir == dir_to_check:  # Достигли корня файловой системы
                break

            dir_to_check = parent_dir

            # Считаем, сколько маркеров проекта нашли
            project_markers_found = sum(
                1
                for marker in project_markers
                if os.path.exists(os.path.join(dir_to_check, marker))
            )

            if project_markers_found >= 1:
                logger.info(f"Корень проекта обнаружен в: {dir_to_check}")
                return dir_to_check

        # Если не удалось найти, используем директорию скрипта
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logger.warning(
            f"Корень проекта не обнаружен. Используем директорию скрипта: {script_dir}"
        )
        return script_dir
