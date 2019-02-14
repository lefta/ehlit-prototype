from typing import Iterator, List, Optional, Text, Tuple, Union


class File(object):
    name: Text


class SourceLocation(object):
    column: int
    file: File
    line: int


class TokenKind(object):
    IDENTIFIER: 'TokenKind'
    KEYWORD: 'TokenKind'
    LITERAL: 'TokenKind'


class Token(object):
    kind: TokenKind
    spelling: Text


class TokenGroup(object):
    TOKENIZE_KEEP_WHITESPACE: int


class TypeKind(object):
    name: str
    INVALID: 'TypeKind'
    UNEXPOSED: 'TypeKind'
    VOID: 'TypeKind'
    BOOL: 'TypeKind'
    CHAR_U: 'TypeKind'
    UCHAR: 'TypeKind'
    CHAR16: 'TypeKind'
    CHAR32: 'TypeKind'
    USHORT: 'TypeKind'
    UINT: 'TypeKind'
    ULONG: 'TypeKind'
    ULONGLONG: 'TypeKind'
    UINT128: 'TypeKind'
    CHAR_S: 'TypeKind'
    SCHAR: 'TypeKind'
    WCHAR: 'TypeKind'
    SHORT: 'TypeKind'
    INT: 'TypeKind'
    LONG: 'TypeKind'
    LONGLONG: 'TypeKind'
    INT128: 'TypeKind'
    FLOAT: 'TypeKind'
    DOUBLE: 'TypeKind'
    LONGDOUBLE: 'TypeKind'
    NULLPTR: 'TypeKind'
    OVERLOAD: 'TypeKind'
    DEPENDENT: 'TypeKind'
    OBJCID: 'TypeKind'
    OBJCCLASS: 'TypeKind'
    OBJCSEL: 'TypeKind'
    FLOAT128: 'TypeKind'
    HALF: 'TypeKind'
    COMPLEX: 'TypeKind'
    POINTER: 'TypeKind'
    BLOCKPOINTER: 'TypeKind'
    LVALUEREFERENCE: 'TypeKind'
    RVALUEREFERENCE: 'TypeKind'
    RECORD: 'TypeKind'
    ENUM: 'TypeKind'
    TYPEDEF: 'TypeKind'
    OBJCINTERFACE: 'TypeKind'
    OBJCOBJECTPOINTER: 'TypeKind'
    FUNCTIONNOPROTO: 'TypeKind'
    FUNCTIONPROTO: 'TypeKind'
    CONSTANTARRAY: 'TypeKind'
    VECTOR: 'TypeKind'
    INCOMPLETEARRAY: 'TypeKind'
    VARIABLEARRAY: 'TypeKind'
    DEPENDENTSIZEDARRAY: 'TypeKind'
    MEMBERPOINTER: 'TypeKind'
    AUTO: 'TypeKind'
    ELABORATED: 'TypeKind'
    PIPE: 'TypeKind'
    OCLIMAGE1DRO: 'TypeKind'
    OCLIMAGE1DARRAYRO: 'TypeKind'
    OCLIMAGE1DBUFFERRO: 'TypeKind'
    OCLIMAGE2DRO: 'TypeKind'
    OCLIMAGE2DARRAYRO: 'TypeKind'
    OCLIMAGE2DDEPTHRO: 'TypeKind'
    OCLIMAGE2DARRAYDEPTHRO: 'TypeKind'
    OCLIMAGE2DMSAARO: 'TypeKind'
    OCLIMAGE2DARRAYMSAARO: 'TypeKind'
    OCLIMAGE2DMSAADEPTHRO: 'TypeKind'
    OCLIMAGE2DARRAYMSAADEPTHRO: 'TypeKind'
    OCLIMAGE3DRO: 'TypeKind'
    OCLIMAGE1DWO: 'TypeKind'
    OCLIMAGE1DARRAYWO: 'TypeKind'
    OCLIMAGE1DBUFFERWO: 'TypeKind'
    OCLIMAGE2DWO: 'TypeKind'
    OCLIMAGE2DARRAYWO: 'TypeKind'
    OCLIMAGE2DDEPTHWO: 'TypeKind'
    OCLIMAGE2DARRAYDEPTHWO: 'TypeKind'
    OCLIMAGE2DMSAAWO: 'TypeKind'
    OCLIMAGE2DARRAYMSAAWO: 'TypeKind'
    OCLIMAGE2DMSAADEPTHWO: 'TypeKind'
    OCLIMAGE2DARRAYMSAADEPTHWO: 'TypeKind'
    OCLIMAGE3DWO: 'TypeKind'
    OCLIMAGE1DRW: 'TypeKind'
    OCLIMAGE1DARRAYRW: 'TypeKind'
    OCLIMAGE1DBUFFERRW: 'TypeKind'
    OCLIMAGE2DRW: 'TypeKind'
    OCLIMAGE2DARRAYRW: 'TypeKind'
    OCLIMAGE2DDEPTHRW: 'TypeKind'
    OCLIMAGE2DARRAYDEPTHRW: 'TypeKind'
    OCLIMAGE2DMSAARW: 'TypeKind'
    OCLIMAGE2DARRAYMSAARW: 'TypeKind'
    OCLIMAGE2DMSAADEPTHRW: 'TypeKind'
    OCLIMAGE2DARRAYMSAADEPTHRW: 'TypeKind'
    OCLIMAGE3DRW: 'TypeKind'
    OCLSAMPLER: 'TypeKind'
    OCLEVENT: 'TypeKind'
    OCLQUEUE: 'TypeKind'
    OCLRESERVEID: 'TypeKind'


class Type(object):
    fully_qualified_name: Text
    kind: TypeKind
    spelling: Text
    element_count: int
    element_type: 'Type'

    def argument_types(self) -> Iterator['Type']:
        pass

    def get_canonical(self) -> 'Type':
        pass

    def get_declaration(self) -> 'Cursor':
        pass

    def get_pointee(self) -> 'Type':
        pass

    def get_result(self) -> 'Type':
        pass

    def is_const_qualified(self) -> bool:
        pass

    def is_volatile_qualified(self) -> bool:
        pass

    def is_restrict_qualified(self) -> bool:
        pass

    def get_size(self) -> int:
        pass

    def is_function_variadic(self) -> bool:
        pass

    def get_fields(self) -> List['Cursor']:
        pass


class AvailabilityKind(object):
    NOT_ACCESSIBLE: 'AvailabilityKind'
    NOT_AVAILABLE: 'AvailabilityKind'


class AccessSpecifier(object):
    PRIVATE: 'AccessSpecifier'
    PROTECTED: 'AccessSpecifier'
    PUBLIC: 'AccessSpecifier'


class CursorKind(object):
    name: Text

    @staticmethod
    def get_all_kinds() -> List['CursorKind']:
        pass

    def is_expression(self) -> bool:
        pass

    def is_statement(self) -> bool:
        pass

    ANNOTATE_ATTR: 'CursorKind'
    CLASS_DECL: 'CursorKind'
    CLASS_TEMPLATE: 'CursorKind'
    COMPOUND_STMT: 'CursorKind'
    CONSTRUCTOR: 'CursorKind'
    CONVERSION_FUNCTION: 'CursorKind'
    CXX_BASE_SPECIFIER: 'CursorKind'
    CXX_METHOD: 'CursorKind'
    DECL_REF_EXPR: 'CursorKind'
    ENUM_CONSTANT_DECL: 'CursorKind'
    ENUM_DECL: 'CursorKind'
    FIELD_DECL: 'CursorKind'
    FRIEND_DECL: 'CursorKind'
    FUNCTION_DECL: 'CursorKind'
    FUNCTION_TEMPLATE: 'CursorKind'
    LAMBDA_EXPR: 'CursorKind'
    MACRO_DEFINITION: 'CursorKind'
    NAMESPACE: 'CursorKind'
    NAMESPACE_REF: 'CursorKind'
    NO_DECL_FOUND: 'CursorKind'
    PARM_DECL: 'CursorKind'
    STRUCT_DECL: 'CursorKind'
    TRANSLATION_UNIT: 'CursorKind'
    TYPEDEF_DECL: 'CursorKind'
    TYPE_REF: 'CursorKind'
    VAR_DECL: 'CursorKind'


class Cursor(object):
    access_specifier: AccessSpecifier
    availability: AvailabilityKind
    brief_comment: Text
    canonical: 'Cursor'
    displayname: Text
    kind: CursorKind
    location: SourceLocation
    mangled_name: Text
    referenced: 'Cursor'
    semantic_parent: 'Cursor'
    spelling: Text
    type: Type
    underlying_typedef_type: Type

    def get_arguments(self) -> Iterator['Cursor']:
        pass

    def get_children(self) -> Iterator['Cursor']:
        pass

    def get_tokens(self) -> Iterator[Token]:
        pass

    def get_definition(self) -> Optional['Cursor']:
        pass

    def is_abstract_record(self) -> bool:
        pass

    def is_const_method(self) -> bool:
        pass

    def is_definition(self) -> bool:
        pass

    def is_implicit(self) -> bool:
        pass

    def is_move_constructor(self) -> bool:
        pass

    def is_scoped_enum(self) -> bool:
        pass

    def is_static_method(self) -> bool:
        pass


class Index(object):
    @staticmethod
    def create(excludeDecls: bool =False) -> 'Index':
        pass

    def parse(self, path: str, args: Optional[List[str]] =None,
              unsaved_files: Union[List[Tuple[str, str]], Optional[str]] =None,
              options: int =0) -> 'TranslationUnit':
        pass


class Diagnostic(object):
    children: Iterator['Diagnostic']

    def format(self, options: Optional[int]=None) -> Text:
        pass


class TranslationUnit(object):
    PARSE_DETAILED_PROCESSING_RECORD: int

    cursor: Cursor
    diagnostics: Iterator[Diagnostic]

    @classmethod
    def from_ast_file(cls, filename: Text, index: Optional[Index]=None) -> 'TranslationUnit':
        pass

    @classmethod
    def from_source(self, path: str, args: Optional[List[str]] =None,
                    unsaved_files: Optional[str] =None, options: int =0,
                    index: Optional[Index] =None) -> 'TranslationUnit':
        pass


class TranslationUnitLoadError(Exception):
    pass
