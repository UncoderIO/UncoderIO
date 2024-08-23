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
from typing import Optional

from app.translator.core.custom_types.meta_info import SeverityType
from app.translator.core.mapping import SourceMapping
from app.translator.core.models.platform_details import PlatformDetails
from app.translator.core.models.query_container import MetaInfoContainer, MitreInfoContainer
from app.translator.managers import render_manager
from app.translator.platforms.microsoft.const import DEFAULT_MICROSOFT_SENTINEL_RULE, microsoft_sentinel_rule_details
from app.translator.platforms.microsoft.mapping import MicrosoftSentinelMappings, microsoft_sentinel_rule_mappings
from app.translator.platforms.microsoft.query_container import SentinelYamlRuleMetaInfoContainer
from app.translator.platforms.microsoft.renders.microsoft_sentinel import (
    MicrosoftSentinelFieldValueRender,
    MicrosoftSentinelQueryRender,
)
from app.translator.tools.utils import get_rule_description_str

_AUTOGENERATED_TEMPLATE = "Autogenerated Microsoft Sentinel Rule"
_SEVERITIES_MAP = {
    SeverityType.critical: SeverityType.high,
    SeverityType.high: SeverityType.high,
    SeverityType.medium: SeverityType.medium,
    SeverityType.low: SeverityType.low,
}


class MicrosoftSentinelRuleFieldValueRender(MicrosoftSentinelFieldValueRender):
    details: PlatformDetails = microsoft_sentinel_rule_details


@render_manager.register
class MicrosoftSentinelRuleRender(MicrosoftSentinelQueryRender):
    details: PlatformDetails = microsoft_sentinel_rule_details
    mappings: MicrosoftSentinelMappings = microsoft_sentinel_rule_mappings
    or_token = "or"
    field_value_render = MicrosoftSentinelRuleFieldValueRender(or_token=or_token)

    def __create_mitre_threat(self, mitre_attack: MitreInfoContainer) -> tuple[list, list]:
        tactics = set()
        techniques = []

        for tactic in mitre_attack.tactics:
            tactics.add(tactic.name)

        for technique in mitre_attack.techniques:
            if technique.tactic:
                for tactic in technique.tactic:
                    tactics.add(tactic)
            techniques.append(technique.technique_id)

        return sorted(tactics), sorted(techniques)

    def finalize_query(
        self,
        prefix: str,
        query: str,
        functions: str,
        meta_info: Optional[MetaInfoContainer] = None,
        source_mapping: Optional[SourceMapping] = None,  # noqa: ARG002
        not_supported_functions: Optional[list] = None,
        unmapped_fields: Optional[list[str]] = None,
        *args,  # noqa: ARG002
        **kwargs,  # noqa: ARG002
    ) -> str:
        query = super().finalize_query(prefix=prefix, query=query, functions=functions)
        rule = copy.deepcopy(DEFAULT_MICROSOFT_SENTINEL_RULE)
        rule["query"] = query
        rule["displayName"] = meta_info.title or _AUTOGENERATED_TEMPLATE
        rule["description"] = get_rule_description_str(
            description=meta_info.description or rule["description"] or _AUTOGENERATED_TEMPLATE,
            author=meta_info.author,
            license_=meta_info.license,
        )
        rule["severity"] = _SEVERITIES_MAP.get(meta_info.severity, SeverityType.medium)
        mitre_tactics, mitre_techniques = self.__create_mitre_threat(mitre_attack=meta_info.mitre_attack)
        rule["tactics"] = mitre_tactics
        rule["techniques"] = mitre_techniques
        if meta_info and isinstance(meta_info, SentinelYamlRuleMetaInfoContainer):
            rule["queryFrequency"] = meta_info.query_frequency or rule["queryFrequency"]
            rule["queryPeriod"] = meta_info.query_period or rule["queryPeriod"]
            rule["triggerOperator"] = meta_info.trigger_operator or rule["triggerOperator"]
            rule["triggerThreshold"] = meta_info.trigger_threshold or rule["triggerThreshold"]
        json_rule = json.dumps(rule, indent=4, sort_keys=False)
        json_rule = self.wrap_with_unmapped_fields(json_rule, unmapped_fields)
        return self.wrap_with_not_supported_functions(json_rule, not_supported_functions)
