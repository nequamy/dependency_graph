import graphviz
import logging
from .project_analyzer import ProjectAnalyzer
from .project_structure import ProjectStructure


class DependencyGraphBuilder:
    """Строит граф зависимостей на основе проанализированных модулей."""

    def __init__(
        self,
        analyzer: ProjectAnalyzer,
        reverse_arrows: bool = True,
        logger: logging.Logger = None,
    ) -> None:
        """
        Инициализирует построитель графа.

        Args:
            analyzer: Анализатор проекта с информацией о модулях и зависимостях
            reverse_arrows: Обратить направление стрелок (True - показывает, кто использует модуль)
        """
        self.analyzer = analyzer
        self.reverse_arrows = reverse_arrows
        self.logger = logger

    def build_graph(self) -> graphviz.Digraph:
        """Строит ориентированный граф зависимостей с улучшенной визуализацией."""
        graph = graphviz.Digraph(
            name="python_imports",
            comment="Python Import Dependencies",
            format="svg",
            engine="dot",
        )

        # Улучшенные глобальные атрибуты графа для минимизации пересечений
        graph.attr(
            rankdir="TB",  # Компоновка сверху вниз
            splines="curved",  # Изогнутые линии для лучшей визуализации
            fontsize="12",
            fontname="Arial",
            nodesep="1.0",  # Увеличенное расстояние между узлами
            ranksep="2.0",  # Увеличенное расстояние между рангами
            overlap="false",  # Предотвращение перекрытия узлов
            compound="true",  # Разрешение составных рёбер между кластерами
            bgcolor="white",  # Белый фон
            pad="1.5",  # Увеличенный отступ для лучшей компоновки
            concentrate="true",  # Объединение общих сегментов рёбер
            # Важные атрибуты для минимизации пересечений:
            ordering="out",  # Упорядочение узлов для уменьшения пересечений
            sep="+25,25",  # Увеличение минимального расстояния между узлами
            mclimit="2.0",  # Увеличение итераций компоновки
            pack="true",  # Упаковка несвязанных компонентов
            packmode="cluster",  # Режим упаковки кластеров для лучшего расположения
        )

        # Создание кластеров с улучшенным стилем
        clusters = {}
        for cluster_name in set(
            self.analyzer.project_structure.cluster_mappings.values()
        ):
            idx = list(self.analyzer.project_structure.cluster_mappings.values()).index(
                cluster_name
            )
            color = ProjectStructure.CLUSTER_COLORS[
                idx % len(ProjectStructure.CLUSTER_COLORS)
            ]

            subgraph = graphviz.Digraph(name=f"cluster_{cluster_name}")
            subgraph.attr(
                label=cluster_name,
                style="filled,rounded",  # Добавлены скругленные углы
                fillcolor=color,
                fontcolor="#333333",  # Темно-серый цвет шрифта
                fontsize="16",
                fontname="Arial Bold",
                color="#88888860",  # Полупрозрачная рамка
                penwidth="1.5",
                margin="20",  # Увеличенные отступы
                labeljust="l",  # Выравнивание метки по левому краю
            )
            clusters[cluster_name] = subgraph

        # Добавление узлов в соответствующие кластеры
        added_nodes = set()

        # Группируем модули по кластерам для лучшей структуризации
        cluster_modules = {}
        for cluster_name in set(
            self.analyzer.project_structure.cluster_mappings.values()
        ):
            cluster_modules[cluster_name] = []

        for module in self.analyzer.modules.values():
            cluster_modules[module.cluster].append(module)

        # Добавляем узлы, сортируя их внутри кластера для лучшей организации
        for cluster_name, modules in cluster_modules.items():
            # Сортируем модули по имени для более организованного расположения
            modules.sort(key=lambda m: m.module_name)

            for module in modules:
                if module.file_path not in added_nodes:
                    label = self.analyzer.get_node_label(
                        module.file_path, module.cluster
                    )

                    # Добавляем узел с улучшенным стилем
                    clusters[module.cluster].node(
                        module.file_path,
                        label=label,
                        shape="box",
                        style="filled,rounded",  # Скругленные углы для узлов
                        fillcolor="white",
                        fontcolor="#333333",  # Темно-серый текст
                        fontsize="11",
                        fontname="Arial",
                        height="0.4",
                        margin="0.15,0.1",
                        penwidth="1.0",  # Более тонкая обводка
                    )
                    added_nodes.add(module.file_path)

        # Добавление всех кластеров в основной граф в определенном порядке
        for cluster_name in self.analyzer.project_structure.cluster_order:
            if cluster_name in clusters:
                graph.subgraph(clusters[cluster_name])

        # Добавление рёбер между узлами с улучшенным стилем
        for dep in self.analyzer.dependencies:
            source = dep.source_module.file_path
            target = dep.target_module.file_path

            if source == target:
                continue  # Пропускаем самоссылки

            # Улучшенный стиль стрелок с изогнутыми линиями
            edge_attrs = {
                "fontsize": "9",
                "fontname": "Arial",
                "fontcolor": "#555555",
                "penwidth": "0.7",  # Более тонкие линии
                "arrowsize": "0.6",  # Маленькие наконечники стрелок
                "color": "#55555570",  # Полупрозрачные стрелки
                "arrowhead": "vee",  # Стильный наконечник стрелки
                "constraint": "true",  # Сохранять иерархию (важно для уменьшения пересечений)
                "weight": "1.5",  # Предпочтительный вес для важных соединений
            }

            if dep.imported_objects:
                # Структурированное отображение импортируемых объектов
                if len(dep.imported_objects) > 3:
                    label = f"{', '.join(dep.imported_objects[:3])}..."
                else:
                    label = ", ".join(dep.imported_objects)
                edge_attrs["label"] = label
                edge_attrs["labeltooltip"] = ", ".join(
                    dep.imported_objects
                )  # Всплывающая подсказка

            # Обратное направление стрелок в зависимости от параметра
            if self.reverse_arrows:
                graph.edge(target, source, **edge_attrs)
            else:
                graph.edge(source, target, **edge_attrs)

        self.logger.info(
            f"Создан граф с {len(added_nodes)} узлами и {len(self.analyzer.dependencies)} рёбрами"
        )
        return graph
