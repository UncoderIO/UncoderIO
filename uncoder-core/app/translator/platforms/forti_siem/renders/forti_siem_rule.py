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

import re
from typing import Optional, Union

from app.translator.const import DEFAULT_VALUE_TYPE
from app.translator.core.const import QUERY_TOKEN_TYPE
from app.translator.core.custom_types.meta_info import SeverityType
from app.translator.core.custom_types.tokens import GroupType, LogicalOperatorType, OperatorType
from app.translator.core.custom_types.values import ValueType
from app.translator.core.mapping import SourceMapping
from app.translator.core.mitre import MitreInfoContainer
from app.translator.core.models.platform_details import PlatformDetails
from app.translator.core.models.query_container import MetaInfoContainer, TokenizedQueryContainer
from app.translator.core.models.query_tokens.field_value import FieldValue
from app.translator.core.models.query_tokens.identifier import Identifier
from app.translator.core.render import BaseFieldValueRender, PlatformQueryRender
from app.translator.core.str_value_manager import StrValue
from app.translator.managers import render_manager
from app.translator.platforms.forti_siem.const import (
    FORTI_SIEM_RULE,
    SOURCES_EVENT_TYPES_CONTAINERS_MAP,
    forti_siem_rule_details,
)
from app.translator.platforms.forti_siem.mapping import FortiSiemMappings, forti_siem_rule_mappings
from app.translator.platforms.forti_siem.str_value_manager import forti_siem_str_value_manager
from app.translator.tools.utils import concatenate_str, get_rule_description_str

_AUTOGENERATED_TEMPLATE = "Autogenerated FortiSIEM Rule"
_EVENT_TYPE_FIELD = "eventType"

_SEVERITIES_MAP = {
    SeverityType.informational: "1",
    SeverityType.low: "3",
    SeverityType.medium: "5",
    SeverityType.high: "7",
    SeverityType.critical: "9",
}

_NOT_OPERATORS_MAP_SUBSTITUTES = {
    OperatorType.EQ: OperatorType.NOT_EQ,
    OperatorType.CONTAINS: OperatorType.NOT_CONTAINS,
    OperatorType.STARTSWITH: OperatorType.NOT_STARTSWITH,
    OperatorType.ENDSWITH: OperatorType.NOT_ENDSWITH,
    OperatorType.REGEX: OperatorType.NOT_REGEX,
}

_NOT_STR_FIELDS = [
    # int
    "ruleId",
    "procTrustLevel",
    "destIpPort",
    "eventAction",
    "srcIpPort",
    "winLogonType",
    "msgLen",
    "size",
    # ip
    "destIpAddr",
    "srcIpAddr",
]


class FortiSiemFieldValueRender(BaseFieldValueRender):
    details: PlatformDetails = forti_siem_rule_details
    str_value_manager = forti_siem_str_value_manager

    and_token = " AND "

    def equal_modifier(self, field: str, value: DEFAULT_VALUE_TYPE) -> str:
        if isinstance(value, list):
            return f"({self.or_token.join([self.equal_modifier(field=field, value=v) for v in value])})"

        if isinstance(value, StrValue):
            if value.has_spec_symbols:
                return self.regex_modifier(field, value)

            value = forti_siem_str_value_manager.from_container_to_str(value)
        return f"{field}={value}" if field in _NOT_STR_FIELDS else f'{field}="{value}"'

    def not_equal_modifier(self, field: str, value: DEFAULT_VALUE_TYPE) -> str:
        if isinstance(value, list):
            return f"({self.and_token.join([self.not_equal_modifier(field=field, value=v) for v in value])})"

        if isinstance(value, StrValue):
            if value.has_spec_symbols:
                return self.not_regex_modifier(field, value)

            value = forti_siem_str_value_manager.from_container_to_str(value)
        return f"{field}!={value}" if field in _NOT_STR_FIELDS else f'{field}!="{value}"'

    @staticmethod
    def __prepare_regex_value(value: DEFAULT_VALUE_TYPE) -> str:
        if isinstance(value, StrValue):
            value = forti_siem_str_value_manager.from_container_to_str(value, value_type=ValueType.regex_value)

        return value

    def contains_modifier(self, field: str, value: DEFAULT_VALUE_TYPE) -> str:
        if isinstance(value, list):
            return f"({self.or_token.join([self.contains_modifier(field=field, value=v) for v in value])})"

        value = self.__prepare_regex_value(value)
        return f'{field} REGEXP "{value}"'

    def not_contains_modifier(self, field: str, value: DEFAULT_VALUE_TYPE) -> str:
        if isinstance(value, list):
            return f"({self.and_token.join([self.not_contains_modifier(field=field, value=v) for v in value])})"

        value = self.__prepare_regex_value(value)
        return f'{field} NOT REGEXP "{value}"'

    def endswith_modifier(self, field: str, value: DEFAULT_VALUE_TYPE) -> str:
        if isinstance(value, list):
            return f"({self.or_token.join([self.endswith_modifier(field=field, value=v) for v in value])})"

        value = self.__prepare_regex_value(value)
        return f'{field} REGEXP "{value}$"'

    def not_endswith_modifier(self, field: str, value: DEFAULT_VALUE_TYPE) -> str:
        if isinstance(value, list):
            return f"({self.and_token.join([self.not_endswith_modifier(field=field, value=v) for v in value])})"

        value = self.__prepare_regex_value(value)
        return f'{field} NOT REGEXP "{value}$"'

    def startswith_modifier(self, field: str, value: DEFAULT_VALUE_TYPE) -> str:
        if isinstance(value, list):
            return f"({self.or_token.join([self.startswith_modifier(field=field, value=v) for v in value])})"

        value = self.__prepare_regex_value(value)
        return f'{field} REGEXP "^{value}"'

    def not_startswith_modifier(self, field: str, value: DEFAULT_VALUE_TYPE) -> str:
        if isinstance(value, list):
            return f"({self.and_token.join([self.not_startswith_modifier(field=field, value=v) for v in value])})"

        value = self.__prepare_regex_value(value)
        return f'{field} NOT REGEXP "^{value}"'

    def regex_modifier(self, field: str, value: DEFAULT_VALUE_TYPE) -> str:
        if isinstance(value, list):
            return f"({self.or_token.join([self.regex_modifier(field=field, value=v) for v in value])})"

        value = self.__prepare_regex_value(value)
        return f'{field} REGEXP "{value}"'

    def not_regex_modifier(self, field: str, value: DEFAULT_VALUE_TYPE) -> str:
        if isinstance(value, list):
            return f"({self.and_token.join([self.not_regex_modifier(field=field, value=v) for v in value])})"

        value = self.__prepare_regex_value(value)
        return f'{field} NOT REGEXP "{value}"'


@render_manager.register
class FortiSiemRuleRender(PlatformQueryRender):
    details: PlatformDetails = forti_siem_rule_details
    mappings: FortiSiemMappings = forti_siem_rule_mappings

    or_token = "OR"
    and_token = "AND"
    not_token = None

    group_token = "(%s)"

    field_value_render = FortiSiemFieldValueRender(or_token=or_token)

    @staticmethod
    def __is_negated_token(prev_token: QUERY_TOKEN_TYPE) -> bool:
        return isinstance(prev_token, Identifier) and prev_token.token_type == LogicalOperatorType.NOT

    @staticmethod
    def __should_negate(is_negated_token: bool = False, negation_ctx: bool = False) -> bool:
        if is_negated_token and negation_ctx:
            return False

        return is_negated_token or negation_ctx

    @staticmethod
    def __negate_token(token: QUERY_TOKEN_TYPE) -> None:
        if isinstance(token, Identifier):
            if token.token_type == LogicalOperatorType.AND:
                token.token_type = LogicalOperatorType.OR
            elif token.token_type == LogicalOperatorType.OR:
                token.token_type = LogicalOperatorType.AND
        elif isinstance(token, FieldValue):
            token_type = token.operator.token_type
            token.operator.token_type = _NOT_OPERATORS_MAP_SUBSTITUTES.get(token_type) or token_type

    def __replace_not_tokens(self, tokens: list[QUERY_TOKEN_TYPE]) -> list[QUERY_TOKEN_TYPE]:
        not_token_indices = []
        negation_ctx_stack = []
        for index, token in enumerate(tokens[1:], start=1):
            current_negation_ctx = negation_ctx_stack[-1] if negation_ctx_stack else False
            prev_token = tokens[index - 1]
            if is_negated_token := self.__is_negated_token(prev_token):
                not_token_indices.append(index - 1)

            if isinstance(token, Identifier):
                if token.token_type == GroupType.L_PAREN:
                    negation_ctx_stack.append(self.__should_negate(is_negated_token, current_negation_ctx))
                    continue
                if token.token_type == GroupType.R_PAREN:
                    if negation_ctx_stack:
                        negation_ctx_stack.pop()
                    continue

            if self.__should_negate(is_negated_token, current_negation_ctx):
                self.__negate_token(token)

        for index in reversed(not_token_indices):
            tokens.pop(index)

        return tokens

    def _generate_from_tokenized_query_container_by_source_mapping(
        self, query_container: TokenizedQueryContainer, source_mapping: SourceMapping
    ) -> str:
        unmapped_fields = self.mappings.check_fields_mapping_existence(
            query_container.meta_info.query_fields,
            query_container.meta_info.function_fields_map,
            self.platform_functions.manager.supported_render_names,
            source_mapping,
        )
        is_event_type_set = False
        field_values = [token for token in query_container.tokens if isinstance(token, FieldValue)]
        mapped_fields_set = set()
        for field_value in field_values:
            mapped_fields = self.mappings.map_field(field_value.field, source_mapping)
            mapped_fields_set = mapped_fields_set.union(set(mapped_fields))
            if _EVENT_TYPE_FIELD in mapped_fields:
                is_event_type_set = True
                self.__update_event_type_values(field_value, source_mapping.source_id)

        tokens = self.__replace_not_tokens(query_container.tokens)
        result = self.generate_query(tokens=tokens, source_mapping=source_mapping)
        prefix = "" if is_event_type_set else self.generate_prefix(source_mapping.log_source_signature)
        rendered_functions = self.generate_functions(query_container.functions.functions, source_mapping)
        not_supported_functions = query_container.functions.not_supported + rendered_functions.not_supported
        return self.finalize_query(
            prefix=prefix,
            query=result,
            functions=rendered_functions.rendered,
            not_supported_functions=not_supported_functions,
            unmapped_fields=unmapped_fields,
            meta_info=query_container.meta_info,
            source_mapping=source_mapping,
            fields=mapped_fields_set,
        )

    @staticmethod
    def __update_event_type_values(field_value: FieldValue, source_id: str) -> None:
        new_values = []
        for value in field_value.values:
            if not str(value).isdigit():
                new_values.append(value)

            elif not (source_event_types_container := SOURCES_EVENT_TYPES_CONTAINERS_MAP.get(source_id, {})):
                new_values.append(f"Win-.*-{value}[^\d]*")
                field_value.operator = Identifier(token_type=OperatorType.REGEX)

            elif event_types := source_event_types_container.event_types_map.get(value, []):
                new_values.extend(event_types)

            else:
                new_values.append(f"{source_event_types_container.default_pattern}{value}-.*")
                field_value.operator = Identifier(token_type=OperatorType.REGEX)

        field_value.values = new_values

    def finalize_query(
        self,
        prefix: str,
        query: str,
        functions: str,
        meta_info: Optional[MetaInfoContainer] = None,
        source_mapping: Optional[SourceMapping] = None,  # noqa: ARG002
        not_supported_functions: Optional[list] = None,
        unmapped_fields: Optional[list[str]] = None,
        fields: Optional[set[str]] = None,
        *args,  # noqa: ARG002
        **kwargs,  # noqa: ARG002
    ) -> str:
        query = super().finalize_query(prefix=prefix, query=query, functions=functions)
        rule = FORTI_SIEM_RULE.replace("<header_placeholder>", self.generate_rule_header(meta_info))
        title = meta_info.title or _AUTOGENERATED_TEMPLATE
        rule = rule.replace("<name_placeholder>", self.generate_rule_name(title))
        rule = rule.replace("<title_placeholder>", self.generate_title(title))
        description = get_rule_description_str(
            description=meta_info.description.replace("\n", " ") or _AUTOGENERATED_TEMPLATE,
            rule_id=meta_info.id,
            author=meta_info.author,
            license_=meta_info.license,
            references=meta_info.references,
        )
        rule = rule.replace("<description_placeholder>", description)
        rule = rule.replace("<incident_def_placeholder>", self.generate_event_type(title, meta_info.severity))
        args_list = self.get_args_list(fields.copy())
        rule = rule.replace("<args_list_placeholder>", self.get_args_str(args_list))
        rule = rule.replace("<query_placeholder>", query)
        rule = rule.replace("<group_by_attr_placeholder>", ", ".join(args_list))
        rule = rule.replace("<attr_list_placeholder>", self.get_attr_str(fields.copy()))
        rule = self.wrap_with_unmapped_fields(rule, unmapped_fields)
        return self.wrap_with_not_supported_functions(rule, not_supported_functions)

    @staticmethod
    def get_attr_str(fields: set[str]) -> str:
        fields.discard("hostName")
        fields.discard("eventType")
        fields.discard("phRecvTime")
        fields = sorted(fields)

        if len(fields) == 0:
            return "phRecvTime, rawEventMsg"

        return ", ".join(["phRecvTime", *fields, "rawEventMsg"])

    @staticmethod
    def get_args_str(fields: list[str]) -> str:
        return ", ".join(f"{f} = Filter.{f}" for f in fields)

    @staticmethod
    def get_args_list(fields: set[str]) -> list[str]:
        fields.discard("eventType")
        fields.add("hostName")
        return sorted(fields)

    @staticmethod
    def generate_event_type(title: str, severity: str) -> str:
        title = title.replace(" ", "_")
        return concatenate_str(f'eventType="PH_RULE_{title}"', f'severity="{_SEVERITIES_MAP[severity]}"')

    @staticmethod
    def generate_title(title: str) -> str:
        return re.sub(r"\s*[^a-zA-Z0-9 _-]+\s*", " ", title)

    @staticmethod
    def generate_rule_name(title: str) -> str:
        # rule name allows only a-zA-Z0-9 \/:.$-
        rule_name = re.sub(r'\s*[^a-zA-Z0-9 /:.$_\'"-]+\s*', " ", title)
        rule_name = re.sub("_", "-", rule_name)
        return re.sub(r'[\'"()+,]*', "", rule_name)

    @staticmethod
    def get_mitre_info(mitre_attack: Union[MitreInfoContainer, None]) -> tuple[str, str]:
        if not mitre_attack:
            return "", ""
        tactics = set()
        techniques = set()
        for tactic in mitre_attack.tactics:
            if tactic_name := tactic.name:
                tactics.add(tactic_name)

        for tech in mitre_attack.techniques:
            techniques.add(tech.technique_id)
            tactics = tactics.union(set(tech.tactic))

        return ", ".join(sorted(tactics)), ", ".join(sorted(techniques))

    def generate_rule_header(self, meta_info: MetaInfoContainer) -> str:
        header = 'group="PH_SYS_RULE_THREAT_HUNTING"'
        tactics_str, techniques_str = self.get_mitre_info(meta_info.mitre_attack)
        if tactics_str:
            header = concatenate_str(header, f'subFunction="{tactics_str}"')

        if techniques_str:
            header = concatenate_str(header, f'technique="{techniques_str}"')

        return concatenate_str(header, 'phIncidentCategory="Server" function="Security"')

    def wrap_with_comment(self, value: str) -> str:
        return f"<!-- {value} -->"
