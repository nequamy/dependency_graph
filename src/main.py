#!/usr/bin/env python3
"""
Python Import Dependency Analyzer

Анализирует зависимости импортов в Python-проекте и генерирует
SVG-диаграмму, отображающую взаимосвязи между файлами и модулями.

Использование:
    python deps.py [--project-root PATH] [--output FILENAME]

Требования:
    - Python 3.8+
    - graphviz package (pip install graphviz)
    - Graphviz software установленный в системе
"""

import argparse
import logging
import os
import sys
import yaml
from typing import Dict, Optional
from include.dependency_graph_builder import DependencyGraphBuilder
from include.project_analyzer import ProjectAnalyzer
from include.project_detector import ProjectDetector
from include.project_structure import ProjectStructure

try:
    import graphviz
except ImportError:
    print("Error: graphviz package is not installed. Run 'pip install graphviz'")
    sys.exit(1)
try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print(
        "Warning: PyYAML package is not installed. Config file support will be disabled."
    )
    print("Run 'pip install pyyaml' to enable configuration file support.")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_config(config_path: Optional[str] = None) -> Dict:
    """
    Загружает конфигурацию проекта из YAML-файла, если он существует.

    Args:
        config_path: Путь к конфигурационному файлу

    Returns:
        Словарь с настройками или пустой словарь, если файл не найден или PyYAML не установлен
    """
    # Если PyYAML не установлен, возвращаем пустой словарь
    if not YAML_AVAILABLE:
        if config_path:
            logger.warning(
                "PyYAML не установлен. Не удается загрузить конфигурационный файл."
            )
        return {}

    # Если путь указан и файл существует
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Не удалось загрузить конфигурационный файл: {e}")
            return {}

    # Проверяем стандартные имена конфигурационных файлов
    default_configs = [
        "deps.yml",
        "deps.yaml",
        "import_analyzer.yml",
        "import_analyzer.yaml",
    ]

    for config_name in default_configs:
        if os.path.exists(config_name):
            try:
                with open(config_name, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.warning(f"Не удалось загрузить {config_name}: {e}")

    # Возвращаем пустой словарь, если конфигурационный файл не найден
    return {}


def main() -> None:
    """Основная функция для анализа импортов и генерации диаграммы зависимостей."""
    parser = argparse.ArgumentParser(
        description="Анализирует зависимости импортов в Python и генерирует SVG диаграмму"
    )
    parser.add_argument(
        "--project-root",
        help="Корневая директория проекта (определяется автоматически, если не указана)",
    )
    parser.add_argument(
        "--output",
        default="import_diagram",
        help="Имя выходного файла (без расширения)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Включить подробное логирование"
    )
    parser.add_argument(
        "--direction",
        choices=["TB", "LR", "BT", "RL"],
        default="TB",
        help="Направление графа: TB (сверху-вниз), LR (слева-направо), BT (снизу-вверх), RL (справа-налево)",
    )
    parser.add_argument(
        "--normal-arrows",
        action="store_true",
        help="Использовать стандартное направление стрелок (от импортирующего к импортируемому модулю)",
    )
    parser.add_argument(
        "--config", help="Путь к конфигурационному YAML-файлу с настройками проекта"
    )
    parser.add_argument(
        "--root-package",
        help="Имя корневого пакета проекта (определяется автоматически, если не указано)",
    )
    parser.add_argument(
        "--engine",
        choices=["dot", "neato", "fdp", "twopi", "circo"],
        default="dot",
        help="Алгоритм компоновки графа: dot (иерархический), neato (пружинный), fdp (силовой), twopi (радиальный), circo (круговой)",
    )

    args = parser.parse_args()

    # Настройка уровня логирования
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Проверка установки Graphviz
    try:
        graphviz_version = os.popen("dot -V").read()
        if graphviz_version:
            logger.info(f"Graphviz обнаружен: {graphviz_version.strip()}")
        else:
            logger.warning(
                "Не удалось определить версию Graphviz, но продолжаем работу"
            )
    except Exception:
        logger.warning("Не удалось проверить установку Graphviz")

    # Загрузка конфигурации
    config = load_config(args.config)

    # Определение корневой директории проекта
    project_root = ProjectDetector.find_project_root(args.project_root)

    # Определение структуры проекта
    if args.root_package or "root_package" in config:
        # Если указан корневой пакет в аргументах или конфигурации
        root_package = args.root_package or config.get("root_package")

        # Если указана структура кластеров в конфигурации
        if "cluster_mappings" in config:
            cluster_mappings = config["cluster_mappings"]
            project_structure = ProjectStructure(root_package, cluster_mappings)
        else:
            # Создаем структуру только с корневым пакетом
            project_structure = ProjectStructure(root_package)
    else:
        # Автоматическое определение структуры проекта
        project_structure = ProjectDetector.detect_project_structure(project_root)

    logger.info(f"Используется корневой пакет: {project_structure.root_package_name}")
    logger.info(
        f"Определены кластеры: {list(project_structure.cluster_mappings.values())}"
    )

    # Создание и запуск анализатора проекта
    analyzer = ProjectAnalyzer(project_root, project_structure)
    analyzer.load_modules()
    analyzer.analyze_imports()

    if not analyzer.dependencies:
        logger.warning("Зависимости между модулями проекта не найдены.")
        # Создаем простую диаграмму-заполнитель
        graph = graphviz.Digraph(
            name="python_imports",
            comment="Зависимости между модулями не найдены",
            format="svg",
        )
        graph.attr(rankdir=args.direction, fontsize="16")
        graph.node(
            "placeholder",
            "Зависимости не найдены",
            shape="box",
            style="filled,rounded",
            fillcolor="#f5f5f5",
        )
    else:
        # Создание и отрисовка графа зависимостей
        graph_builder = DependencyGraphBuilder(
            analyzer, reverse_arrows=not args.normal_arrows
        )
        graph = graph_builder.build_graph()
        graph.engine = args.engine  # Устанавливаем выбранный движок
        # Переопределяем направление графа если указано в параметрах
        graph.attr(rankdir=args.direction)

    try:
        # Явно задаем формат
        graph.format = "svg"
        output_file = f"{args.output}.gv"

        # Сначала сохраняем DOT-файл для возможной отладки
        graph.save(output_file)
        logger.info(f"Сгенерирован DOT-файл: {output_file}")

        # Затем рендерим в SVG с улучшенными настройками
        output_path = graph.render(args.output, format="svg", cleanup=False)
        logger.info(f"Сгенерирована SVG-диаграмма: {output_path}")

        # Проверка размера файла
        file_size = os.path.getsize(output_path)
        logger.info(f"Размер SVG-файла: {file_size} байт")

        # Открываем SVG в браузере на macOS
        if sys.platform == "darwin":
            try:
                os.system(f"open {output_path}")
            except Exception as e:
                logger.warning(f"Не удалось открыть SVG: {e}")
    except Exception as e:
        logger.error(f"Не удалось сгенерировать SVG-диаграмму: {e}")
        logger.error(
            "Убедитесь, что Graphviz установлен в вашей системе: https://graphviz.org/download/"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
