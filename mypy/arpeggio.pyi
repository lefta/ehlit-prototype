from typing import Callable, Generic, Iterable, List, Tuple, TypeVar, Union
import typing
import re

T = TypeVar('T')

# These could be improved a lot once mypy supports recursive grammars
TokenType = Union['ParsingExpression', str, Callable[[], object], List[object]]
GrammarType = Union[TokenType, Iterable[TokenType], Iterable[object]]


class ParseTreeNode:
    position: int


class ParsingExpression:
    def __init__(self, *elements: TokenType, **kwargs: Union[str, bool]) -> None:
        pass


class NoMatch(Exception):
    position: int
    rules: List[ParsingExpression]


class Repetition(ParsingExpression):
    def __init__(self, *elements: TokenType, **kwargs: Union[str, bool]) -> None:
        pass


class Optional(Repetition):
    pass


class ZeroOrMore(Repetition):
    pass


class OneOrMore(Repetition):
    pass


class EOF(ParsingExpression):
    pass


class Match(ParsingExpression):
    pass


class RegExMatch(Match):
    def __init__(self, to_match: str, rule_name: str ='', root: bool =False,
                 ignore_case: typing.Optional[bool] =None, multiline: typing.Optional[bool] =None,
                 str_repr: typing.Optional[str] =None, re_flags: re.RegexFlag =re.MULTILINE
                 ) -> None:
        pass


class StrMatch(Match):
    pass


class Sequence(ParsingExpression):
    def __init__(self, *elements: TokenType, **kwargs: Union[str, bool]) -> None:
        pass


class Not(ParsingExpression):
    pass


class And(ParsingExpression):
    pass


class Parser:
    def parse(self, text: str) -> ParseTreeNode:
        pass


class ParserPython(Parser):
    file_name: str

    def __init__(self, fun: Callable[[], GrammarType], comments: Callable[[], GrammarType],
                 debug: bool = True, **kwargs: bool) -> None:
        pass

    def parse_file(self, file_name: str) -> ParseTreeNode:
        pass

    def pos_to_linecol(self, pos: int) -> Tuple[int, int]:
        pass


class PTNodeVisitor(Generic[T]):
    pass


def visit_parse_tree(parse_tree: ParseTreeNode, visitor: PTNodeVisitor[T]) -> T:
    pass
