#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

int32_t const* const EF9print_intcrcB3int(int32_t const* const i)
{
    return (i);
}

void EF11update_ptrsxrB5int32xrB3int(int32_t* restrict i, int32_t* restrict j)
{
}

void EF6strcpyxB3strcxB3str(char* restrict s1, char* const restrict s2)
{
}

void EF7strncpyxB3strcxB3strB4size(char* restrict s1, char* const restrict s2, size_t n)
{
}
int32_t volatile EwV13some_register;
int32_t volatile EwV19some_other_register = *((int32_t*)42);

int32_t main(void)
{
    int32_t const i = 42;
    int32_t const* const j = EF9print_intcrcB3int(&i);
    int32_t const* k = &i;
    int32_t l = 21;
    int32_t* const m = &l;
    return (0);
}
