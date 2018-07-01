#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

int32_t* ref_call(void)
{
    return (NULL);
}

void inc(int32_t* nb)
{
    if (!nb)
    {
        return;
    }
    *nb += 1;
}

void inner_parens(int32_t i)
{
    if (!0)
    {
        i = 1;
        if (!0)
        {
            i = 2;
        }
        i = 3;
    }
    i = 4;
    if (0)
    {
        i = 5;
    }
}

int32_t main(int32_t ac, char** av)
{
    puts("Hello, world!\n");
    printf("With some mathematics: 4 * 8 = %d", 4 * 8);
    ref_call();
    return (0);
}
