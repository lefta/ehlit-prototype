include c_parser/macro.h

str call_macros() {
  int i = MACROFUNC(1, 2)
  str s = MACROFUNC_NO_BODY("Hello", "World")
  i = CONSTANT
  i = VALUE
  i = MACROCEPTION
  return MACROFUNC(i, s)
}
