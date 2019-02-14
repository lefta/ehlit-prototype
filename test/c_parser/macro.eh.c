#include <stddef.h>
#include <stdint.h>
#include <c_parser/macro.h>

char* _EF11call_macros(void)
{
    int32_t i = MACROFUNC(1, 2);
    char* s = MACROFUNC_NO_BODY("Hello", "World");
    i = CONSTANT;
    i = VALUE;
    i = CONSTANT;
    return (MACROFUNC(i, s));
}
