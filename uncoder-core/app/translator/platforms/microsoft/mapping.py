from typing import Optional

from app.translator.core.mapping import BasePlatformMappings, LogSourceSignature
from app.translator.platforms.microsoft.const import (
    microsoft_defender_query_details,
    microsoft_sentinel_query_details,
    microsoft_sentinel_rule_details,
)


class MicrosoftSentinelLogSourceSignature(LogSourceSignature):
    def __init__(self, tables: Optional[list[str]], default_source: dict):
        self.tables = set(tables or [])
        self._default_source = default_source or {}

    def is_suitable(self, table: Optional[list[str]] = None) -> bool:
        return self._check_conditions([set(table).issubset(self.tables) if table else None])

    def __str__(self) -> str:
        return self._default_source.get("table", "")


class MicrosoftSentinelMappings(BasePlatformMappings):
    def prepare_log_source_signature(self, mapping: dict) -> MicrosoftSentinelLogSourceSignature:
        tables = mapping.get("log_source", {}).get("table")
        default_log_source = mapping["default_log_source"]
        return MicrosoftSentinelLogSourceSignature(tables=tables, default_source=default_log_source)


microsoft_sentinel_query_mappings = MicrosoftSentinelMappings(
    platform_dir="microsoft_sentinel", platform_details=microsoft_sentinel_query_details
)
microsoft_sentinel_rule_mappings = MicrosoftSentinelMappings(
    platform_dir="microsoft_sentinel", platform_details=microsoft_sentinel_rule_details
)


class MicrosoftDefenderLogSourceSignature(MicrosoftSentinelLogSourceSignature):
    pass


class MicrosoftDefenderMappings(MicrosoftSentinelMappings):
    is_strict_mapping = True

    def prepare_log_source_signature(self, mapping: dict) -> MicrosoftDefenderLogSourceSignature:
        tables = mapping.get("log_source", {}).get("table")
        default_log_source = mapping["default_log_source"]
        return MicrosoftDefenderLogSourceSignature(tables=tables, default_source=default_log_source)


microsoft_defender_query_mappings = MicrosoftDefenderMappings(
    platform_dir="microsoft_defender", platform_details=microsoft_defender_query_details
)
