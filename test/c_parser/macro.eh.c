#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <c_parser/macro.h>

MACRO_TYPE_STR _EF11call_macros(void)
{
    MACRO_TYPE_INT i = MACROFUNC(1, 2);
    MACRO_TYPE_STR s = MACROFUNC_NO_BODY("Hello", "World");
    i = CONSTANT;
    i = VALUE;
    i = CONSTANT;
    return (MACROFUNC(i, s));
}
