#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

int32_t main(int32_t ac, char** av)
{
    char** av2 = av;
    ac--;
    while (ac)
    {
        ac--;
        av2[ac] = av[ac + 1];
        puts(av[ac]);
    }
    int32_t** arr1;
    int32_t arr42[42][5];
    return (0);
}
