#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

int32_t main(int32_t ac, char** av)
{
    printf("%d\n", ((int32_t)&av));
    void* test = ((char*)ac);
    size_t i = ((size_t*)av)[0];
    return (0);
}
