#include <stddef.h>
#include <stdint.h>
typedef int32_t _ET2nb;
typedef void _ET7nothing;
typedef void(* _ET3pfn)(_ET2nb);

_ET7nothing _EF3incrB3int(int32_t* number)
{
    if (!number)
    {
        return;
    }
    *number += 1;
}

void _EF10do_nothingT2nb(_ET2nb n)
{
}

_ET2nb main(void)
{
    _ET2nb i = 42;
    _ET3pfn pdn = &_EF10do_nothingT2nb;
    _EF3incrB3int(&i);
    _EF10do_nothingT2nb(i);
    pdn(i);
    return (i);
}
