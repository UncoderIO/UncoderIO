from typing import Optional

from app.translator.core.mapping import BasePlatformMappings, LogSourceSignature


class AQLLogSourceSignature(LogSourceSignature):
    def __init__(
        self,
        device_types: Optional[list[int]],
        categories: Optional[list[int]],
        qids: Optional[list[int]],
        qid_event_categories: Optional[list[int]],
        default_source: dict,
    ):
        self.device_types = set(device_types or [])
        self.categories = set(categories or [])
        self.qids = set(qids or [])
        self.qid_event_categories = set(qid_event_categories or [])
        self._default_source = default_source or {}

    def is_suitable(
        self,
        devicetype: Optional[list[int]] = None,
        category: Optional[list[int]] = None,
        qid: Optional[list[int]] = None,
        qideventcategory: Optional[list[int]] = None,
    ) -> bool:
        conditions = [
            set(devicetype).issubset(self.device_types) if devicetype else None,
            set(category).issubset(self.categories) if category else None,
            set(qid).issubset(self.qids) if qid else None,
            set(qideventcategory).issubset(self.qid_event_categories) if qideventcategory else None,
        ]
        return self._check_conditions(conditions)

    def __str__(self) -> str:
        return self._default_source.get("table", "events")

    @property
    def extra_condition(self) -> str:
        default_source = self._default_source
        extra = []
        for key, value in default_source.items():
            if key != "table" and value:
                _condition = f"{key}={value}" if isinstance(value, int) else f"{key}='{value}'"
                extra.append(_condition)
        return " AND ".join(extra)


class AQLMappings(BasePlatformMappings):
    skip_load_default_mappings: bool = False
    extend_default_mapping_with_all_fields: bool = True

    def prepare_log_source_signature(self, mapping: dict) -> AQLLogSourceSignature:
        log_source = mapping.get("log_source", {})
        default_log_source = mapping["default_log_source"]
        return AQLLogSourceSignature(
            device_types=log_source.get("devicetype"),
            categories=log_source.get("category"),
            qids=log_source.get("qid"),
            qid_event_categories=log_source.get("qideventcategory"),
            default_source=default_log_source,
        )
