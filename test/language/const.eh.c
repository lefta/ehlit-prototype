#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

int32_t const* const print_int(int32_t const* const i)
{
    printf("%d\n", *i);
    return (i);
}

int32_t main(void)
{
    int32_t const i = 42;
    int32_t const* const j = print_int(&i);
    int32_t const* k = &i;
    int32_t l = 21;
    int32_t* const m = &l;
    return (0);
}
