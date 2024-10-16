"""
Uncoder IO Commercial Edition License
-----------------------------------------------------------------
Copyright (c) 2024 SOC Prime, Inc.

This file is part of the Uncoder IO Commercial Edition ("CE") and is
licensed under the Uncoder IO Non-Commercial License (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://github.com/UncoderIO/UncoderIO/blob/main/LICENSE

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-----------------------------------------------------------------
"""

from contextlib import suppress
from datetime import timedelta
from typing import Optional, Union

import isodate
from isodate.isoerror import ISO8601Error

from app.translator.core.mixins.rule import JsonRuleMixin, YamlRuleMixin
from app.translator.core.models.platform_details import PlatformDetails
from app.translator.core.models.query_container import (
    MetaInfoContainer,
    MitreInfoContainer,
    RawMetaInfoContainer,
    RawQueryContainer,
)
from app.translator.managers import parser_manager
from app.translator.platforms.microsoft.const import (
    microsoft_sentinel_rule_details,
    microsoft_sentinel_yaml_rule_details,
)
from app.translator.platforms.microsoft.mapping import MicrosoftSentinelMappings, microsoft_sentinel_rule_mappings
from app.translator.platforms.microsoft.parsers.microsoft_sentinel import MicrosoftSentinelQueryParser
from app.translator.tools.utils import parse_rule_description_str


@parser_manager.register
class MicrosoftSentinelRuleParser(MicrosoftSentinelQueryParser, JsonRuleMixin):
    details: PlatformDetails = microsoft_sentinel_rule_details
    mappings: MicrosoftSentinelMappings = microsoft_sentinel_rule_mappings

    @staticmethod
    def _parse_timeframe(raw_timeframe: Optional[str]) -> Optional[timedelta]:
        with suppress(ISO8601Error):
            return isodate.parse_duration(raw_timeframe)

    def parse_raw_query(self, text: str, language: str) -> RawQueryContainer:
        rule = self.load_rule(text=text)
        tags = []
        mitre_attack = self.mitre_config.get_mitre_info(
            tactics=[tactic.lower() for tactic in rule.get("tactics", [])],
            techniques=[technique.lower() for technique in rule.get("techniques", [])],
        )

        if mitre_attack:
            for technique in mitre_attack.techniques:
                tags.append(technique.technique_id.lower())
            for tactic in mitre_attack.tactics:
                tags.append(tactic.name.lower().replace(" ", "_"))
        parsed_description = parse_rule_description_str(rule.get("description", ""))

        return RawQueryContainer(
            query=rule["query"],
            language=language,
            meta_info=MetaInfoContainer(
                id_=parsed_description.get("rule_id"),
                title=rule.get("displayName"),
                description=parsed_description.get("description") or rule.get("description"),
                timeframe=self._parse_timeframe(rule.get("queryFrequency", "")),
                severity=rule.get("severity", "medium"),
                mitre_attack=mitre_attack,
                author=parsed_description.get("author") or [rule.get("author")],
                license_=parsed_description.get("license"),
                tags=tags,
                references=parsed_description.get("references"),
            ),
        )


@parser_manager.register
class MicrosoftSentinelYAMLRuleParser(YamlRuleMixin, MicrosoftSentinelRuleParser):
    details: PlatformDetails = microsoft_sentinel_yaml_rule_details
    mappings: MicrosoftSentinelMappings = microsoft_sentinel_rule_mappings

    def extract_tags(self, data: Union[dict, list, str]) -> list[str]:
        tags = []
        if isinstance(data, dict):
            for key, value in data.items():
                tags.extend(self.extract_tags(value))
        elif isinstance(data, list):
            for item in data:
                tags.extend(self.extract_tags(item))
        elif isinstance(data, str):
            tags.append(data)
        return tags

    def __get_tags_from_required_data_connectors(self, required_data_connectors: dict) -> list[str]:
        return list(self.extract_tags(required_data_connectors))

    def __get_tags_from_metadata(self, metadata: dict) -> list[str]:
        fields_to_process = {}
        for k, v in metadata.items():
            if k.lower() != "author":
                fields_to_process[k] = v

        return list(self.extract_tags(fields_to_process))

    def parse_raw_query(self, text: str, language: str) -> RawQueryContainer:
        rule = self.load_rule(text=text)
        tags = []
        mitre_attack: MitreInfoContainer = self.mitre_config.get_mitre_info(
            tactics=[tactic.lower() for tactic in rule.get("tactics", [])],
            techniques=[technique.lower() for technique in rule.get("relevantTechniques", [])],
        )

        if mitre_attack:
            for technique in mitre_attack.techniques:
                tags.append(technique.technique_id.lower())
            for tactic in mitre_attack.tactics:
                tags.append(tactic.name.lower().replace(" ", "_"))

        tags.extend(self.__get_tags_from_required_data_connectors(rule.get("requiredDataConnectors", {})))
        tags.extend(self.__get_tags_from_metadata(rule.get("metadata", {})))

        for tag in rule.get("tags", []):
            if isinstance(tag, str):
                tags.append(tag)

        timeframe = self._parse_timeframe(rule.get("queryFrequency", ""))
        query_period = self._parse_timeframe(rule.get("queryPeriod", ""))

        return RawQueryContainer(
            query=rule["query"],
            language=language,
            meta_info=MetaInfoContainer(
                id_=rule.get("id"),
                title=rule.get("name"),
                description=rule.get("description"),
                timeframe=timeframe,
                query_period=query_period,
                severity=rule.get("severity", "medium").lower(),
                mitre_attack=mitre_attack,
                author=rule.get("metadata", {}).get("author", {}).get("name", "").split(","),
                tags=sorted(set(tags)),
                raw_metainfo_container=RawMetaInfoContainer(
                    trigger_operator=rule.get("triggerOperator"),
                    trigger_threshold=rule.get("triggerThreshold"),
                    query_frequency=rule.get("queryFrequency"),
                    query_period=rule.get("queryPeriod"),
                ),
            ),
        )
