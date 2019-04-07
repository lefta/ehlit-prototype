#include <stddef.h>
#include <stdint.h>

int32_t const* const _EF9print_intcrcB3int(int32_t const* const i)
{
    return (i);
}

void _EF11update_ptrsxrB5int32xrB3int(int32_t* restrict i, int32_t* restrict j)
{
}

void _EF6strcpyxB3strcxB3str(char* restrict s1, char* const restrict s2)
{
}

void _EF7strncpyxB3strcxB3strB4size(char* restrict s1, char* const restrict s2, size_t n)
{
}
int32_t volatile _EwV13some_register;
int32_t volatile _EwV19some_other_register = *((int32_t*)42);

int32_t main(void)
{
    int32_t const i = 42;
    int32_t const* const j = _EF9print_intcrcB3int(&i);
    int32_t const* k = &i;
    int32_t l = 21;
    int32_t* const m = &l;
    return (0);
}
