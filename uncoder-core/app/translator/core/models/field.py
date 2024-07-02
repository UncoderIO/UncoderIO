from typing import Optional, Union

from app.translator.core.custom_types.tokens import STR_SEARCH_OPERATORS, OperatorType
from app.translator.core.mapping import DEFAULT_MAPPING_NAME, SourceMapping
from app.translator.core.models.identifier import Identifier
from app.translator.core.str_value_manager import StrValue


class Alias:
    def __init__(self, name: str):
        self.name = name


class Field:
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.__generic_names_map = {}

    def get_generic_field_name(self, source_id: str) -> Optional[str]:
        return self.__generic_names_map.get(source_id)

    def add_generic_names_map(self, generic_names_map: dict) -> None:
        self.__generic_names_map = generic_names_map

    def set_generic_names_map(self, source_mappings: list[SourceMapping], default_mapping: SourceMapping) -> None:
        generic_names_map = {
            source_mapping.source_id: source_mapping.fields_mapping.get_generic_field_name(self.source_name)
            or self.source_name
            for source_mapping in source_mappings
        }
        if DEFAULT_MAPPING_NAME not in generic_names_map:
            fields_mapping = default_mapping.fields_mapping
            generic_names_map[DEFAULT_MAPPING_NAME] = (
                fields_mapping.get_generic_field_name(self.source_name) or self.source_name
            )

        self.__generic_names_map = generic_names_map


class PredefinedField:
    def __init__(self, name: str):
        self.name = name


class FieldField:
    def __init__(
        self,
        source_name_left: str,
        operator: Identifier,
        source_name_right: str,
        is_alias_left: bool = False,
        is_alias_right: bool = False,
    ):
        self.field_left = Field(source_name=source_name_left) if not is_alias_left else None
        self.alias_left = Alias(name=source_name_left) if is_alias_left else None
        self.operator = operator
        self.field_right = Field(source_name=source_name_right) if not is_alias_right else None
        self.alias_right = Alias(name=source_name_right) if is_alias_right else None


class FieldValue:
    def __init__(
        self,
        source_name: str,
        operator: Identifier,
        value: Union[int, str, StrValue, list, tuple],
        is_alias: bool = False,
        is_predefined_field: bool = False,
    ):
        # mapped by platform fields mapping
        self.field = Field(source_name=source_name) if not (is_alias or is_predefined_field) else None
        # not mapped
        self.alias = Alias(name=source_name) if is_alias else None
        # mapped by platform predefined fields mapping
        self.predefined_field = PredefinedField(name=source_name) if is_predefined_field else None

        self.operator = operator
        self.values = []
        self.__add_value(value)

    @property
    def value(self) -> Union[int, str, StrValue, list[Union[int, str, StrValue]]]:
        if isinstance(self.values, list) and len(self.values) == 1:
            return self.values[0]
        return self.values

    @value.setter
    def value(self, new_value: Union[int, str, StrValue, list[Union[int, str, StrValue]]]) -> None:
        self.values = []
        self.__add_value(new_value)

    def __add_value(self, value: Optional[Union[int, str, StrValue, list, tuple]]) -> None:
        if value and isinstance(value, (list, tuple)):
            for v in value:
                self.__add_value(v)
        elif (
            value
            and isinstance(value, str)
            and value.isnumeric()
            and self.operator.token_type not in STR_SEARCH_OPERATORS
        ):
            self.values.append(int(value))
        elif value is not None and isinstance(value, (int, str)):
            self.values.append(value)

    def __repr__(self):
        if self.alias:
            return f"{self.alias.name} {self.operator.token_type} {self.values}"

        if self.predefined_field:
            return f"{self.predefined_field.name} {self.operator.token_type} {self.values}"

        return f"{self.field.source_name} {self.operator.token_type} {self.values}"


class Keyword:
    def __init__(self, value: Union[str, list[str]]):
        self.operator: Identifier = Identifier(token_type=OperatorType.KEYWORD)
        self.name = "keyword"
        self.values = []
        self.__add_value(value=value)

    @property
    def value(self) -> Union[str, list[str]]:
        if isinstance(self.values, list) and len(self.values) == 1:
            return self.values[0]
        return self.values

    def __add_value(self, value: Union[str, list[str]]) -> None:
        if value and isinstance(value, (list, tuple)):
            self.values.extend(value)
        elif value and isinstance(value, str):
            self.values.append(value)

    def __repr__(self):
        return f"{self.name} {self.operator.token_type} {self.values}"
