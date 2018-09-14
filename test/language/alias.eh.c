#include <stddef.h>
#include <stdint.h>
typedef int32_t nb;
typedef void nothing;
typedef void(* pfn)(nb);

nothing inc(int32_t* number)
{
    if (!number)
    {
        return;
    }
    *number += 1;
}

void do_nothing(nb n)
{
}

nb main(void)
{
    nb i = 42;
    pfn pdn = &do_nothing;
    inc(&i);
    do_nothing(i);
    pdn(i);
    return (i);
}
