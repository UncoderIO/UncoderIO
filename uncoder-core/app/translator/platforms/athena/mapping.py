from typing import Optional

from app.translator.core.mapping import DEFAULT_MAPPING_NAME, BasePlatformMappings, LogSourceSignature, SourceMapping
from app.translator.platforms.athena.const import athena_query_details


class AthenaLogSourceSignature(LogSourceSignature):
    def __init__(self, tables: Optional[list[str]], default_source: dict):
        self.tables = set(tables or [])
        self._default_source = default_source or {}

    def is_suitable(self, table: str) -> bool:
        return table in self.tables

    def __str__(self) -> str:
        return self._default_source.get("table", "")


class AthenaMappings(BasePlatformMappings):
    def prepare_log_source_signature(self, mapping: dict) -> AthenaLogSourceSignature:
        tables = mapping.get("log_source", {}).get("table")
        default_log_source = mapping["default_log_source"]
        return AthenaLogSourceSignature(tables=tables, default_source=default_log_source)

    def get_suitable_source_mappings(self, field_names: list[str], table: Optional[str]) -> list[SourceMapping]:
        suitable_source_mappings = []
        for source_mapping in self._source_mappings.values():
            if source_mapping.source_id == DEFAULT_MAPPING_NAME:
                continue

            log_source_signature: AthenaLogSourceSignature = source_mapping.log_source_signature
            if table and log_source_signature.is_suitable(table=table):
                if source_mapping.fields_mapping.is_suitable(field_names):
                    suitable_source_mappings.append(source_mapping)
            elif source_mapping.fields_mapping.is_suitable(field_names):
                suitable_source_mappings.append(source_mapping)

        if not suitable_source_mappings:
            suitable_source_mappings = [self._source_mappings[DEFAULT_MAPPING_NAME]]

        return suitable_source_mappings


athena_query_mappings = AthenaMappings(platform_dir="athena", platform_details=athena_query_details)
