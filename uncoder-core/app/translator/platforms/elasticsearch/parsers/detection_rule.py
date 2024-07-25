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

from app.translator.core.mixins.rule import JsonRuleMixin
from app.translator.core.models.platform_details import PlatformDetails
from app.translator.core.models.query_container import MetaInfoContainer, RawQueryContainer
from app.translator.managers import parser_manager
from app.translator.platforms.elasticsearch.const import elasticsearch_rule_details
from app.translator.platforms.elasticsearch.parsers.elasticsearch import ElasticSearchQueryParser
from app.translator.tools.utils import parse_rule_description_str


@parser_manager.register
class ElasticSearchRuleParser(ElasticSearchQueryParser, JsonRuleMixin):
    details: PlatformDetails = elasticsearch_rule_details

    def parse_raw_query(self, text: str, language: str) -> RawQueryContainer:
        rule = self.load_rule(text=text)
        mitre_attack = {"tactics": [], "techniques": []}
        parsed_description = parse_rule_description_str(rule.get("description", ""))
        if rule_mitre_attack_data := rule.get("threat"):
            for threat_data in rule_mitre_attack_data:
                if technique := self.mitre_config.get_technique(threat_data["technique"][0]["id"].lower()):
                    mitre_attack["techniques"].append(technique)
                if tactic := self.mitre_config.get_tactic(threat_data["tactic"]["name"].replace(" ", "_").lower()):
                    mitre_attack["tactics"].append(tactic)

        return RawQueryContainer(
            query=rule["query"],
            language=language,
            meta_info=MetaInfoContainer(
                id_=rule.get("rule_id"),
                title=rule.get("name"),
                description=parsed_description.get("description") or rule.get("description"),
                references=rule.get("references", []),
                author=parsed_description.get("author") or rule.get("author", ""),
                severity=rule.get("severity"),
                license_=parsed_description.get("license"),
                tags=rule.get("tags"),
                mitre_attack=mitre_attack if mitre_attack["tactics"] or mitre_attack["techniques"] else None,
            ),
        )
