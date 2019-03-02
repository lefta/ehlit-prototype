include c_parser/macro.h

MACRO_TYPE_STR call_macros() {
  MACRO_TYPE_INT i = MACROFUNC(1, 2)
  MACRO_TYPE_STR s = MACROFUNC_NO_BODY("Hello", "World")
  i = CONSTANT
  i = VALUE
  i = MACROCEPTION
  return MACROFUNC(i, s)
}
