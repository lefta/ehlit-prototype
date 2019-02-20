# Copyright © 2017-2019 Cedric Legrand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice (including the next
# paragraph) shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import glob
import logging
import subprocess
from argparse import ArgumentParser
from clang.cindex import (Index, TranslationUnitLoadError, CursorKind, TypeKind, Cursor, Type,
                          TranslationUnit, TokenKind, Token, Config)
from ehlit.parser.error import ParseError, Failure
from ehlit.parser import ast
from typing import Dict, List, Optional, Set

# Find the clang library. On some systems, the clang library is not called `libclang.so`, for
# example on Ubuntu, it is `libclang.so.1`.
proc: subprocess.CompletedProcess = subprocess.run(['llvm-config', '--libdir'],
                                                   stdin=subprocess.PIPE,
                                                   stderr=subprocess.PIPE,
                                                   stdout=subprocess.PIPE,
                                                   encoding='utf-8')

if proc.returncode != 0:
    raise RuntimeError('Could not find LLVM path, make sure it is installed')

clang_libs: List[str] = glob.glob(os.path.join(proc.stdout.strip(), 'libclang.so*'))
if len(clang_libs) is 0:
    raise RuntimeError('Could not find libclang.so, make sure Clang is installed')

Config.set_library_file(clang_libs[0])


include_dirs: List[str] = []

# Add CFLAGS environment variable include dirs
parser: ArgumentParser = ArgumentParser()
parser.add_argument('-I', dest='dirs', default=[], action='append')
try:
    args, unknown = parser.parse_known_args(os.environ['CFLAGS'].split())
    for d in args.dirs:
        include_dirs += d
except KeyError:
    # Silently continue if there is no CFLAGS environment variable
    pass


try:
    # Run clang without input in verbose mode just to get its default include directories to have an
    # environment as close to upcoming build as possible. There will be differences do it like this,
    # but:
    # - We know we have clang as we rely on its library for parsing. At least it becomes a minor
    #   dependency.
    # - It is ways easier and more reliable than supporting each and every system / (cross) compiler
    #   combo out there
    # - They should be quite the same than the ones actually used
    # - Only differences should be minor / internal enough to not have consequences on ehlit code
    proc = subprocess.run(['clang', '-E', '-v', '-'], stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                          stdout=subprocess.PIPE, encoding='utf-8')

    if proc.returncode != 0:
        # Just to stop the execution of the try block
        raise Exception('')

    i1: Optional[int] = None
    i2: Optional[int] = None
    lines: List[str] = proc.stderr.split('\n')
    for i, line in enumerate(lines):
        if line == '#include "..." search starts here:':
            i1 = i
        elif line == 'End of search list.':
            i2 = i

    # Should not happen unless clang changes its output, which is very unlikely
    assert i1 is not None and i2 is not None and i1 < i2
    lines = lines[i1 + 1:i2]
    lines.remove('#include <...> search starts here:')
    include_dirs += [l.strip() for l in lines]

except Exception:
    logging.warning('failed to get default include directories')

# Yups, mixing multiple languages in the same directory would be very disapointing, but who knows...
include_dirs.append('.')


# Build an empty file to get a list of builtin Clang macros. We do not want to expose them, as they
# are too much specific and could change between the Ehlit build and the C build.
def _get_builtin_defines() -> List[str]:
    defs: List[str] = []
    index: Index = Index.create()
    tu: TranslationUnit = index.parse('builtins.h',
                                      options=TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD,
                                      unsaved_files=[('builtins.h', '')])
    for c in tu.cursor.get_children():
        if c.kind == CursorKind.MACRO_DEFINITION:
            toks = list(c.get_tokens())
            defs.append(toks[0].spelling)
    del tu
    del index
    return defs


builtin_defines: List[str] = _get_builtin_defines()


class CDefine(ast.Declaration):
    def __init__(self, sym: ast.Identifier) -> None:
        super().__init__(
            0,
            ast.CompoundIdentifier([ast.Identifier(0, '@any')]),
            sym,
            ast.Qualifier.NONE
        )
        self.declaration_type = ast.DeclarationType.C


class CMacroFunction(ast.FunctionDeclaration):
    def __init__(self, sym: ast.Identifier, arg_cnt: int) -> None:
        super().__init__(
            0,
            ast.Qualifier.NONE,
            ast.TemplatedIdentifier('@func', [ast.FunctionType(
                CAnyType.make(),
                [ast.VariableDeclaration(CAnyType.make(), None)] * arg_cnt
            )]),
            sym
        )
        self.declaration_type = ast.DeclarationType.C


class CAnyType(ast.Type):
    @staticmethod
    def make() -> ast.Symbol:
        return ast.CompoundIdentifier([ast.Identifier(0, '@c_any')])

    @property
    def name(self) -> str:
        return '@c_any'

    def dup(self) -> ast.Type:
        return CAnyType()


uint_types: Set[TypeKind] = {
    TypeKind.UCHAR,
    TypeKind.USHORT,
    TypeKind.UINT,
    TypeKind.ULONG,
    TypeKind.ULONGLONG,
}

int_types: Set[TypeKind] = {
    TypeKind.CHAR_S,
    TypeKind.SCHAR,
    TypeKind.SHORT,
    TypeKind.INT,
    TypeKind.LONG,
    TypeKind.LONGLONG,
}

decimal_types: Dict[TypeKind, str] = {
    TypeKind.FLOAT: '@float',
    TypeKind.DOUBLE: '@double',
    TypeKind.LONGDOUBLE: '@decimal'
}


def cursor_to_ehlit(cursor: Cursor) -> Optional[ast.Node]:
    try:
        return globals()['parse_' + cursor.kind.name](cursor)
    except KeyError:
        logging.debug('c_compat: unimplemented: parse_%s' % cursor.kind.name)
    return None


def type_to_ehlit(typ: Type) -> ast.Node:
    res: Optional[ast.Node] = None
    if typ.kind in uint_types:
        res = ast.CompoundIdentifier([ast.Identifier(0, '@uint' + str(typ.get_size() * 8))])
    elif typ.kind in int_types:
        res = ast.CompoundIdentifier([ast.Identifier(0, '@int' + str(typ.get_size() * 8))])
    elif typ.kind in decimal_types:
        res = ast.CompoundIdentifier([ast.Identifier(0, decimal_types[typ.kind])])
    else:
        try:
            res = globals()['type_' + typ.kind.name](typ)
        except KeyError:
            logging.debug('c_compat: unimplemented: type_%s' % typ.kind.name)
    if res is None:
        return ast.CompoundIdentifier([ast.Identifier(0, '@any')])
    elif not isinstance(res, ast.Symbol):
        return res
    if typ.is_const_qualified():
        res.qualifiers = res.qualifiers | ast.Qualifier.CONST
    if typ.is_volatile_qualified():
        res.qualifiers = res.qualifiers | ast.Qualifier.VOLATILE
    if typ.is_restrict_qualified():
        res.qualifiers = res.qualifiers | ast.Qualifier.RESTRICT
    return res


def value_to_ehlit(val: str, typ: Type) -> Optional[ast.Expression]:
    if typ.kind in uint_types or typ.kind in int_types:
        return ast.Expression([ast.Number(val)], False)
    if typ.kind in decimal_types:
        return ast.Expression([ast.DecimalNumber(val)], False)

    try:
        return globals()['value_' + typ.kind.name](val)
    except KeyError:
        logging.debug('c_compat: unimplemented: value_%s' % typ.kind.name)
    return None


def find_file_in_path(filename: str) -> str:
    for d in include_dirs:
        path = os.path.join(d, filename)
        if os.path.isfile(path):
            return path
    raise ParseError([Failure(ParseError.Severity.Error, 0,
                              '%s: no such file or directory' % filename, None)])


def parse(filename: str) -> List[ast.Node]:
    path: str = find_file_in_path(filename)
    index: Index = Index.create()
    try:
        tu: TranslationUnit = index.parse(path,
                                          options=TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)
    except TranslationUnitLoadError:
        raise ParseError([Failure(ParseError.Severity.Error, 0, '%s: parsing failed' % filename,
                                  None)])
    result: List[ast.Node] = [CAnyType()]
    for c in tu.cursor.get_children():
        node: Optional[ast.Node] = cursor_to_ehlit(c)
        if node is not None:
            result.append(node)
    del tu
    del index
    return result


def parse_VAR_DECL(cursor: Cursor) -> ast.Node:
    assign: Optional[Cursor] = cursor.get_definition()
    value: Optional[ast.Expression] = None
    if assign is not None:
        got_eq: bool = False
        for t in assign.get_tokens():
            if value is not None:
                logging.debug(
                    'c_compat: error: unhandled token while getting value: {}'.format(t.spelling)
                )
            elif got_eq:
                value = value_to_ehlit(t.spelling, cursor.type)
            elif t.spelling == '=':
                got_eq = True
        if got_eq is False:
            logging.debug('c_compat: error: unhandled assignment')
    typ: ast.Node = type_to_ehlit(cursor.type)
    assert isinstance(typ, ast.Symbol)
    return ast.VariableDeclaration(
        typ,
        ast.Identifier(0, cursor.spelling),
        ast.Assignment(value) if value is not None else None
    )


def parse_FUNCTION_DECL(cursor: Cursor) -> ast.Node:
    args: List[ast.VariableDeclaration] = []
    for c in cursor.get_children():
        if c.kind == CursorKind.PARM_DECL:
            typ = type_to_ehlit(c.type)
            assert isinstance(typ, ast.Symbol)
            args.append(ast.VariableDeclaration(typ, ast.Identifier(0, c.spelling)))

    ret_type = type_to_ehlit(cursor.type.get_result())
    assert isinstance(ret_type, ast.Symbol)
    return ast.FunctionDeclaration(
        0,
        ast.Qualifier.NONE,
        ast.TemplatedIdentifier('@func', [ast.FunctionType(
            ret_type,
            args,
            cursor.type.is_function_variadic()
        )]),
        ast.Identifier(0, cursor.spelling)
    )


def parse_TYPEDEF_DECL(cursor: Cursor) -> ast.Node:
    typ: ast.Node = type_to_ehlit(cursor.underlying_typedef_type)
    assert isinstance(typ, ast.Type) or isinstance(typ, ast.Symbol)
    return ast.Alias(typ, ast.Identifier(0, cursor.spelling))


def _parse_container_structure_fields(cursor: Cursor) -> List[ast.VariableDeclaration]:
    fields: List[ast.VariableDeclaration] = []
    for f in cursor.type.get_fields():
        typ: ast.Node = type_to_ehlit(f.type)
        assert isinstance(typ, ast.Symbol)
        fields.append(ast.VariableDeclaration(typ, ast.Identifier(0, f.spelling), None))
    return fields


def parse_STRUCT_DECL(cursor: Cursor) -> ast.Node:
    if not cursor.is_definition():
        return ast.Struct(0, ast.Identifier(0, cursor.spelling), None)
    return ast.Struct(
        0,
        ast.Identifier(0, cursor.spelling),
        _parse_container_structure_fields(cursor)
    )


def parse_UNION_DECL(cursor: Cursor) -> ast.Node:
    if not cursor.is_definition():
        return ast.EhUnion(0, ast.Identifier(0, cursor.spelling), None)
    return ast.EhUnion(
        0,
        ast.Identifier(0, cursor.spelling),
        _parse_container_structure_fields(cursor)
    )


def parse_ENUM_DECL(cursor: Cursor) -> ast.Node:
    if not cursor.is_definition():
        return ast.EhEnum(0, ast.Identifier(0, cursor.spelling), None)
    fields: List[ast.Identifier] = []
    expect: bool = False
    for t in cursor.get_tokens():
        if t.spelling == '{' or t.spelling == ',':
            expect = True
        elif t.spelling == '}':
            break
        elif expect:
            fields.append(ast.Identifier(0, t.spelling))
            expect = False
    return ast.EhEnum(0, ast.Identifier(0, cursor.spelling), fields)


def parse_MACRO_DEFINITION(cursor: Cursor) -> Optional[ast.Node]:
    tokens: List[Token] = list(cursor.get_tokens())
    if tokens[0].spelling in builtin_defines:
        return None

    sym: ast.Identifier = ast.Identifier(0, tokens[0].spelling)

    # Simple define
    if len(tokens) is 1:
        return CDefine(sym)
    # Function macro
    if tokens[1].spelling == '(':
        i = 2
        arg_cnt = 0
        while i < len(tokens):
            if tokens[i].kind != TokenKind.IDENTIFIER or i + 1 >= len(tokens):
                break
            arg_cnt += 1
            if tokens[i + 1].spelling == ')':
                if i + 2 >= len(tokens) and ',' not in [t.spelling for t in tokens]:
                    break
                return CMacroFunction(sym, arg_cnt)
            elif tokens[i + 1].spelling != ',':
                break
            i += 2
    # Constant macro
    next_relevant_token = 2 if tokens[1].spelling == '(' else 1
    if tokens[next_relevant_token].kind == TokenKind.LITERAL:
        return ast.VariableDeclaration(_macro_var_type(tokens), sym)
    # Alias macro
    alias: Optional[ast.Identifier] = _macro_alias_value(tokens)
    if alias is not None:
        return ast.Alias(ast.CompoundIdentifier([alias]), ast.Identifier(0, tokens[0].spelling))
    return None


def _macro_var_type(tokens: List[Token]) -> ast.Symbol:
    for tok in tokens:
        if tok.kind == TokenKind.LITERAL:
            if tok.spelling[0] == '"':
                return ast.CompoundIdentifier([ast.Identifier(0, '@str')])
            if all(x in '0123456789' for x in tok.spelling):
                return ast.CompoundIdentifier([ast.Identifier(0, '@int32')])
            if all(x in '0123456789.' for x in tok.spelling):
                return ast.CompoundIdentifier([ast.Identifier(0, '@float')])
    return CAnyType.make()


def _macro_alias_value(tokens: List[Token]) -> Optional[ast.Identifier]:
    name: str = tokens[0].spelling
    tokens = tokens[2:] if tokens[1].spelling == '(' else tokens[1:]
    if tokens[0].kind == TokenKind.KEYWORD:
        typ: Optional[ast.Identifier] = _macro_alias_type(tokens)
        if type is not None:
            return typ
    elif len(tokens) == 1 or (len(tokens) == 2 and tokens[1].spelling == ')'):
        return ast.Identifier(0, tokens[0].spelling)
    logging.debug('c_parser: failed to parse macro: {}'.format(name))
    return None


def _macro_alias_type(tokens: List[Token]) -> Optional[ast.Identifier]:
    prefix: str = ''
    size: int = 32
    decimal: bool = False
    for t in tokens:
        if t.spelling == 'char':
            size = 8
        elif t.spelling == 'short':
            size = 16
        elif t.spelling == 'long':
            size *= 2
        elif t.spelling == 'float':
            decimal = True
        elif t.spelling == 'double':
            decimal = True
            size *= 2
        elif t.spelling == 'unsigned':
            prefix = 'u'
        elif t.spelling == ')':
            break
        elif t.spelling not in ['signed', 'int']:
            logging.debug('c_parser: unhandled token: {}'.format(t.spelling))
            return None
    if decimal:
        if size == 32:
            return ast.Identifier(0, '@float')
        if size == 64:
            return ast.Identifier(0, '@double')
        if size == 128:
            return ast.Identifier(0, '@decimal')
        return None
    return ast.Identifier(0, '@{}int{}'.format(prefix, size))


def type_VOID(typ: Type) -> ast.Symbol:
    return ast.CompoundIdentifier([ast.Identifier(0, '@void')])


def type_POINTER(typ: Type) -> ast.Node:
    subtype: Type = typ.get_pointee()
    builtin_type: Optional[ast.Symbol] = {
        TypeKind.CHAR_S: ast.CompoundIdentifier([ast.Identifier(0, '@str')]),
        TypeKind.SCHAR: ast.CompoundIdentifier([ast.Identifier(0, '@str')]),
        TypeKind.VOID: ast.CompoundIdentifier([ast.Identifier(0, '@any')])
    }.get(subtype.kind)
    if builtin_type is not None:
        return builtin_type
    res = type_to_ehlit(subtype)
    if isinstance(res, ast.TemplatedIdentifier) and res.name == '@func':
        return res
    assert isinstance(res, ast.Symbol)
    return ast.Reference(res)


def type_TYPEDEF(typ: Type) -> ast.Node:
    return ast.CompoundIdentifier([ast.Identifier(0, typ.get_declaration().spelling)])


def type_CONSTANTARRAY(typ: Type) -> ast.Node:
    elem: ast.Node = type_to_ehlit(typ.element_type)
    assert isinstance(elem, ast.Symbol)
    if typ.element_count == 1:
        return ast.Array(elem, None)
    return ast.Array(elem, ast.Number(str(typ.element_count)))


def type_INCOMPLETEARRAY(typ: Type) -> ast.Node:
    elem: ast.Node = type_to_ehlit(typ.element_type)
    assert isinstance(elem, ast.Symbol)
    return ast.Array(elem, None)


def type_ELABORATED(typ: Type) -> ast.Node:
    decl: Cursor = typ.get_canonical().get_declaration()
    # If the declaration do not have a name, it may not be referenced. In this case, we have to
    # embed the type definition in its usage. Otherwise, we reference it with its identifier.
    if decl.spelling == '':
        res: Optional[ast.Node] = cursor_to_ehlit(decl)
        if res is None:
            # The underlying type is not handled, so make this elaborated type unhandled too
            raise KeyError
        return res
    return ast.CompoundIdentifier([ast.Identifier(0, decl.spelling)])


def type_RECORD(typ: Type) -> ast.Node:
    decl: Cursor = typ.get_declaration()
    # If the type do not have a name, it may not be referenced. In the case, we have to embed
    # the type definition in its usage. Otherwise, we reference it with its identifier.
    if decl.spelling == '':
        res: Optional[ast.Node] = cursor_to_ehlit(decl)
        if res is None:
            # The underlying type is not handled, so make this elaborated type unhandled too
            raise KeyError
        return res
    return ast.CompoundIdentifier([ast.Identifier(0, decl.spelling)])


def type_FUNCTIONPROTO(typ: Type) -> ast.Node:
    args: List[ast.VariableDeclaration] = []
    for a in typ.argument_types():
        res: ast.Node = type_to_ehlit(a)
        assert isinstance(res, ast.Symbol)
        args.append(ast.VariableDeclaration(res, None))
    ret_type: ast.Node = type_to_ehlit(typ.get_result())
    assert isinstance(ret_type, ast.Symbol)
    return ast.TemplatedIdentifier('@func', [ast.FunctionType(ret_type, args)])


def type_UNEXPOSED(typ: Type) -> ast.Node:
    return type_to_ehlit(typ.get_canonical())
