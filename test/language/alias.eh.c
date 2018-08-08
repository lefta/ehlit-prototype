#include <stddef.h>
#include <stdint.h>
typedef int32_t nb;
typedef void nothing;

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
    inc(&i);
    do_nothing(i);
    return (i);
}
