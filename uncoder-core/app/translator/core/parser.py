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

import re
from abc import ABC, abstractmethod
from typing import Optional, Union

from app.translator.core.const import QUERY_TOKEN_TYPE
from app.translator.core.exceptions.parser import TokenizerGeneralException
from app.translator.core.functions import PlatformFunctions
from app.translator.core.mapping import BasePlatformMappings, SourceMapping
from app.translator.core.models.functions.base import Function
from app.translator.core.models.platform_details import PlatformDetails
from app.translator.core.models.query_container import RawQueryContainer, TokenizedQueryContainer
from app.translator.core.models.query_tokens.field import Field
from app.translator.core.models.query_tokens.field_field import FieldField
from app.translator.core.models.query_tokens.field_value import FieldValue
from app.translator.core.models.query_tokens.function_value import FunctionValue
from app.translator.core.tokenizer import QueryTokenizer


class QueryParser(ABC):
    wrapped_with_comment_pattern: str = None
    details: PlatformDetails = None

    def remove_comments(self, text: str) -> str:
        if self.wrapped_with_comment_pattern:
            return re.sub(self.wrapped_with_comment_pattern, "\n", text, flags=re.MULTILINE).strip()

        return text

    def parse_raw_query(self, text: str, language: str) -> RawQueryContainer:
        return RawQueryContainer(query=text, language=language)

    @abstractmethod
    def parse(self, raw_query_container: RawQueryContainer) -> TokenizedQueryContainer:
        raise NotImplementedError("Abstract method")


class PlatformQueryParser(QueryParser, ABC):
    mappings: BasePlatformMappings = None
    tokenizer: QueryTokenizer = None
    platform_functions: PlatformFunctions = None

    def get_query_tokens(self, query: str) -> list[QUERY_TOKEN_TYPE]:
        if not query:
            raise TokenizerGeneralException("Can't translate empty query. Please provide more details")
        return self.tokenizer.tokenize(query=query)

    def get_field_tokens(
        self, query_tokens: list[QUERY_TOKEN_TYPE], functions: Optional[list[Function]] = None
    ) -> list[Field]:
        field_tokens = []
        for token in query_tokens:
            if isinstance(token, FieldValue):
                field_tokens.append(token.field)
            elif isinstance(token, FieldField):
                if token.field_left:
                    field_tokens.append(token.field_left)
                if token.field_right:
                    field_tokens.append(token.field_right)
            elif isinstance(token, FunctionValue):
                field_tokens.extend(self.tokenizer.get_field_tokens_from_func_args([token.function]))

        if functions:
            field_tokens.extend(self.tokenizer.get_field_tokens_from_func_args(functions))

        return field_tokens

    def get_source_mappings(
        self, field_tokens: list[Field], log_sources: dict[str, Union[str, list[str]]]
    ) -> list[SourceMapping]:
        field_names = [field.source_name for field in field_tokens]
        source_mappings = self.mappings.get_suitable_source_mappings(field_names=field_names, **log_sources)
        self.tokenizer.set_field_tokens_generic_names_map(field_tokens, source_mappings, self.mappings.default_mapping)
        return source_mappings
