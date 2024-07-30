"""
Uncoder IO Community Edition License
-----------------------------------------------------------------
Copyright (c) 2024 SOC Prime, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-----------------------------------------------------------------
"""

import copy
import json
from typing import Optional, Union

from app.translator.core.mapping import SourceMapping
from app.translator.core.mitre import MitreConfig, MitreInfoContainer
from app.translator.core.models.platform_details import PlatformDetails
from app.translator.core.models.query_container import MetaInfoContainer
from app.translator.managers import render_manager
from app.translator.platforms.base.lucene.mapping import LuceneMappings
from app.translator.platforms.elasticsearch.const import ELASTICSEARCH_DETECTION_RULE, elasticsearch_rule_details
from app.translator.platforms.elasticsearch.mapping import elasticsearch_rule_mappings
from app.translator.platforms.elasticsearch.renders.elasticsearch import (
    ElasticSearchFieldValue,
    ElasticSearchQueryRender,
)

_AUTOGENERATED_TEMPLATE = "Autogenerated Elastic Rule"


class ElasticSearchRuleFieldValue(ElasticSearchFieldValue):
    details: PlatformDetails = elasticsearch_rule_details


@render_manager.register
class ElasticSearchRuleRender(ElasticSearchQueryRender):
    details: PlatformDetails = elasticsearch_rule_details
    mappings: LuceneMappings = elasticsearch_rule_mappings
    mitre: MitreConfig = MitreConfig()

    or_token = "OR"
    and_token = "AND"
    not_token = "NOT"

    field_value_render = ElasticSearchRuleFieldValue(or_token=or_token)

    def __create_mitre_threat(self, mitre_attack: MitreInfoContainer) -> Union[list, list[dict]]:
        if not mitre_attack.techniques:
            return []
        threat = []

        for tactic in mitre_attack.tactics:
            tactic_render = {"id": tactic.external_id, "name": tactic.name, "reference": tactic.url}
            sub_threat = {"tactic": tactic_render, "framework": "MITRE ATT&CK", "technique": []}
            for technique in mitre_attack.techniques:
                technique_id = technique.technique_id.lower()
                if "." in technique_id:
                    technique_id = technique_id[: technique.technique_id.index(".")]
                main_technique = self.mitre.get_technique(technique_id)
                if tactic.name in main_technique.tactic:
                    sub_threat["technique"].append(
                        {
                            "id": main_technique.technique_id,
                            "name": main_technique.name,
                            "reference": main_technique.url,
                        }
                    )
            if len(sub_threat["technique"]) > 0:
                threat.append(sub_threat)

        return sorted(threat, key=lambda x: x["tactic"]["id"])

    def finalize_query(
        self,
        prefix: str,
        query: str,
        functions: str,
        meta_info: Optional[MetaInfoContainer] = None,
        source_mapping: Optional[SourceMapping] = None,
        not_supported_functions: Optional[list] = None,
        unmapped_fields: Optional[list[str]] = None,
        *args,  # noqa: ARG002
        **kwargs,  # noqa: ARG002
    ) -> str:
        query = super().finalize_query(prefix=prefix, query=query, functions=functions)
        rule = copy.deepcopy(ELASTICSEARCH_DETECTION_RULE)
        index = source_mapping.log_source_signature.default_source.get("index") if source_mapping else None
        rule.update(
            {
                "query": query,
                "description": meta_info.description or rule["description"] or _AUTOGENERATED_TEMPLATE,
                "name": meta_info.title or _AUTOGENERATED_TEMPLATE,
                "rule_id": meta_info.id,
                "author": meta_info.author,
                "severity": meta_info.severity,
                "references": meta_info.references,
                "license": meta_info.license,
                "tags": meta_info.tags,
                "threat": self.__create_mitre_threat(meta_info.mitre_attack),
                "false_positives": meta_info.false_positives,
                "index": [index] if index else [],
            }
        )
        rule_str = json.dumps(rule, indent=4, sort_keys=False, ensure_ascii=False)
        rule_str = self.wrap_with_unmapped_fields(rule_str, unmapped_fields)
        return self.wrap_with_not_supported_functions(rule_str, not_supported_functions)
