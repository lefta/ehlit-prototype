#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
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

nb main(void)
{
    nb i = 42;
    printf("%d\n", i);
    return (i);
}
