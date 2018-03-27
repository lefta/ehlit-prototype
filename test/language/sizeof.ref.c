#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

int32_t main(void)
{
    printf("%i %i %i", sizeof(int32_t), sizeof(int32_t*), sizeof(int32_t*));
    return (0);
}
