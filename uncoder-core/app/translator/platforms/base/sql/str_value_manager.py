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
from typing import ClassVar

from app.translator.core.custom_types.values import ValueType
from app.translator.core.str_value_manager import (
    CONTAINER_SPEC_SYMBOLS_MAP,
    RE_STR_SPEC_SYMBOLS_MAP,
    BaseSpecSymbol,
    ReDigitalSymbol,
    ReWhiteSpaceSymbol,
    ReWordBoundarySymbol,
    ReWordSymbol,
    SingleSymbolWildCard,
    StrValue,
    StrValueManager,
    UnboundLenWildCard,
)
from app.translator.platforms.base.sql.escape_manager import sql_escape_manager

SQL_CONTAINER_SPEC_SYMBOLS_MAP = copy.copy(CONTAINER_SPEC_SYMBOLS_MAP)
SQL_CONTAINER_SPEC_SYMBOLS_MAP.update({SingleSymbolWildCard: "_", UnboundLenWildCard: "%"})


class SQLStrValueManager(StrValueManager):
    escape_manager = sql_escape_manager
    container_spec_symbols_map: ClassVar[dict[type[BaseSpecSymbol], str]] = SQL_CONTAINER_SPEC_SYMBOLS_MAP
    re_str_alpha_num_symbols_map: ClassVar[dict[str, type[BaseSpecSymbol]]] = {
        "b": ReWordBoundarySymbol,
        "w": ReWordSymbol,
        "d": ReDigitalSymbol,
        "s": ReWhiteSpaceSymbol,
    }
    re_str_spec_symbols_map = RE_STR_SPEC_SYMBOLS_MAP
    str_spec_symbols_map: ClassVar[dict[str, type[BaseSpecSymbol]]] = {
        "_": SingleSymbolWildCard,
        "%": UnboundLenWildCard,
    }

    def from_str_to_container(self, value: str) -> StrValue:
        split = []
        prev_char = None
        for char in value:
            if char in self.str_spec_symbols_map:
                split.append(self.str_spec_symbols_map[char]())
            else:
                if char == "'":
                    if prev_char == "'":
                        split.append(char)
                    prev_char = char
                    continue
                split.append(char)

            prev_char = char

        return StrValue(value, self._concat(split))

    def from_re_str_to_container(self, value: str) -> StrValue:
        value = value.replace("''", "'")
        return super().from_re_str_to_container(value)

    def from_container_to_str(self, container: StrValue, value_type: str = ValueType.value) -> str:
        result = ""
        for el in container.split_value:
            if isinstance(el, str):
                result += self.escape_manager.escape(el, value_type)
            elif isinstance(el, BaseSpecSymbol):
                if value_type == ValueType.regex_value:
                    if isinstance(el, SingleSymbolWildCard):
                        result += "."
                        continue
                    if isinstance(el, UnboundLenWildCard):
                        result += ".*"
                        continue

                if pattern := self.container_spec_symbols_map.get(type(el)):
                    result += pattern

        return result


sql_str_value_manager = SQLStrValueManager()
