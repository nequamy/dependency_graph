from dataclasses import dataclass, field
from typing import Dict, Optional

@dataclass
class ProjectStructure:
    """Определяет структуру проекта и соответствующие кластеры."""

    # Цвета для кластеров с повышенной прозрачностью
    CLUSTER_COLORS = [
        "#e41a1c30",  # красный прозрачный
        "#4daf4a30",  # зеленый прозрачный
        "#377eb830",  # синий прозрачный
        "#ff7f0030",  # оранжевый прозрачный
        "#984ea330",  # фиолетовый прозрачный
        "#ffff3330",  # желтый прозрачный
        "#a6562830",  # коричневый прозрачный
        "#f781bf30",  # розовый прозрачный
    ]

    def __init__(
        self, root_package_name: str, cluster_mappings: Optional[Dict[str, str]] = None
    ):
        """
        Инициализирует структуру проекта.

        Args:
            root_package_name: Имя корневого пакета проекта
            cluster_mappings: Словарь маппинга путей к кластерам
        """
        self.root_package_name = root_package_name

        # Словарь маппинга подпутей к кластерам
        self.cluster_mappings = cluster_mappings or {
            "": "Root",  # Корневые файлы
        }

        # Порядок отображения кластеров
        self.cluster_order = list(set(self.cluster_mappings.values()))
        if "Root" in self.cluster_order:
            # Root всегда должен быть первым
            self.cluster_order.remove("Root")
            self.cluster_order.insert(0, "Root")