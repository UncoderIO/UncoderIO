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

from app.translator.core.mapping import LogSourceSignature, SourceMapping
from app.translator.core.mitre import MitreConfig
from app.translator.core.models.platform_details import PlatformDetails
from app.translator.core.models.query_container import MetaInfoContainer, MitreInfoContainer
from app.translator.managers import render_manager
from app.translator.platforms.elasticsearch.const import ESQL_RULE, elasticsearch_esql_rule_details
from app.translator.platforms.elasticsearch.mapping import LuceneMappings, esql_query_mappings
from app.translator.platforms.elasticsearch.renders.esql import ESQLFieldValueRender, ESQLQueryRender

_AUTOGENERATED_TEMPLATE = "Autogenerated ESQL Rule"


class ESQLRuleFieldValueRender(ESQLFieldValueRender):
    details: PlatformDetails = elasticsearch_esql_rule_details


@render_manager.register
class ESQLRuleRender(ESQLQueryRender):
    details: PlatformDetails = elasticsearch_esql_rule_details
    mappings: LuceneMappings = esql_query_mappings
    mitre: MitreConfig = MitreConfig()

    or_token = "or"
    field_value_render = ESQLRuleFieldValueRender(or_token=or_token)

    def generate_prefix(self, log_source_signature: Optional[LogSourceSignature], functions_prefix: str = "") -> str:  # noqa: ARG002
        table = str(log_source_signature) if str(log_source_signature) else "*"
        return f"FROM {table} metadata _id, _version, _index |"

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
                if main_technique and tactic.name in main_technique.tactic:
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
        source_mapping: Optional[SourceMapping] = None,  # noqa: ARG002
        not_supported_functions: Optional[list] = None,
        *args,  # noqa: ARG002
        **kwargs,  # noqa: ARG002
    ) -> str:
        query = super().finalize_query(prefix=prefix, query=query, functions=functions)
        rule = copy.deepcopy(ESQL_RULE)
        rule.update(
            {
                "query": query,
                "description": meta_info.description if meta_info else rule["description"] or _AUTOGENERATED_TEMPLATE,
                "name": meta_info.title if meta_info else _AUTOGENERATED_TEMPLATE,
            }
        )
        if meta_info:
            rule.update(
                {
                    "rule_id": meta_info.id,
                    "author": [meta_info.author],
                    "severity": meta_info.severity,
                    "references": meta_info.references,
                    "license": meta_info.license,
                    "tags": meta_info.tags,
                    "threat": self.__create_mitre_threat(meta_info.mitre_attack),
                    "false_positives": meta_info.false_positives,
                }
            )
        rule_str = json.dumps(rule, indent=4, sort_keys=False, ensure_ascii=False)
        if not_supported_functions:
            rendered_not_supported = self.render_not_supported_functions(not_supported_functions)
            return rule_str + rendered_not_supported
        return rule_str
