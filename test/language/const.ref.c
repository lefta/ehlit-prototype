#include <stddef.h>
#include <stdio.h>

int const* const print_int(int const* const i)
{
    printf("%d\n", *i);
    return (i);
}

int main(void)
{
    int const i = 42;
    int const* const j = print_int(&i);
    int const* k = &i;
    int l = 21;
    int* const m = &l;
    return (0);
}
