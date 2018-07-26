#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

int32_t main(void)
{
    int32_t i = 3;
    while (i)
    {
        printf("looping\n");
        i = i - 1;
    }
    i = 3;
    while (i)
    {
        i = i - 1;
    }
    return (0);
}
