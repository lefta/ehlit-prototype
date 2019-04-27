#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
typedef int32_t ET2nb;
typedef void ET7nothing;
typedef void(* ET3pfn)(ET2nb);

ET7nothing EF3incrB3int(int32_t* number)
{
    if (!number)
    {
        return;
    }
    *number += 1;
}

void EF10do_nothingT2nb(ET2nb n)
{
}

ET2nb main(void)
{
    ET2nb i = 42;
    ET3pfn pdn = &EF10do_nothingT2nb;
    EF3incrB3int(&i);
    EF10do_nothingT2nb(i);
    pdn(i);
    return (i);
}
