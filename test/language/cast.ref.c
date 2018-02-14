#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

int32_t main(int32_t ac, char** av)
{
    printf("%d\n", ((int32_t)&av));
    void* test = ((char*)ac);
    ((char*)test) = av[0];
    int8_t n = 0;
    ((char*)test)[0] = n;
    size_t i = ((size_t*)av)[0];
    return (0);
}
