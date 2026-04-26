from datetime import datetime

from ..config.config_types import ClassifiedItem, Config, ItemClassification, ScannedItem


def classify(
    items: list[ScannedItem], config: Config, now: datetime
) -> list[ClassifiedItem]:
    result: list[ClassifiedItem] = []
    for item in items:
        age_in_days = max(0, (now - item.effective_date).days)

        if any(p in item.name for p in config.ignore_pattern):
            classification: ItemClassification = "ignored"
        elif config.remove_all or any(p in item.name for p in config.removable_pattern):
            classification = "removable"
        else:
            classification = "standard"

        result.append(
            ClassifiedItem(
                item=item,
                classification=classification,
                age_in_days=age_in_days,
            )
        )

    return result
