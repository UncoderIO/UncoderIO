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
from typing import ClassVar

from app.translator.core.str_value_manager import (
    BaseSpecSymbol,
    ReDigitalSymbol,
    ReWhiteSpaceSymbol,
    ReWordSymbol,
    StrValueManager,
)
from app.translator.platforms.elasticsearch.escape_manager import ESQLQueryEscapeManager, esql_query_escape_manager


class ESQLQueryStrValueManager(StrValueManager):
    escape_manager: ESQLQueryEscapeManager = esql_query_escape_manager
    re_str_alpha_num_symbols_map: ClassVar[dict[str, type[BaseSpecSymbol]]] = {
        "w": ReWordSymbol,
        "d": ReDigitalSymbol,
        "s": ReWhiteSpaceSymbol,
    }


esql_query_str_value_manager = ESQLQueryStrValueManager()
