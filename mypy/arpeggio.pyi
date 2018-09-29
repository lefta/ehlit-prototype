from typing import Callable, Generic, List, TypeVar, Union
import typing
import re

T = TypeVar('T')
TokenType = Union['ParsingExpression', str, Callable[[], List[object]], List[object]]

class ParseTree:
    pass

class NoMatch(Exception):
    pass

class ParsingExpression:
    def __init__(self, *elements: TokenType, **kwargs: Union[str, bool]) -> None:
        pass

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
    def parse(self, text: str) -> ParseTree:
        pass

class ParserPython(Parser):
    def __init__(self, fun: Callable[[], TokenType], debug: bool = True, **kwargs: bool) -> None:
        pass
    def parse_file(self, file_name: str) -> ParseTree:
        pass

class PTNodeVisitor(Generic[T]):
    pass

def visit_parse_tree(parse_tree: ParseTree, visitor: PTNodeVisitor[T]) -> T:
    pass
