#include <stddef.h>
#include <stdint.h>

int32_t const* const print_int(int32_t const* const i)
{
    return (i);
}

void update_ptrs(int32_t* restrict i, int32_t* restrict j)
{
}

void strcpy(char* restrict s1, char* const restrict s2)
{
}

void strncpy(char* restrict s1, char* const restrict s2, size_t n)
{
}
int32_t volatile some_register;
int32_t volatile some_other_register = *((int32_t*)42);

int32_t main(void)
{
    int32_t const i = 42;
    int32_t const* const j = print_int(&i);
    int32_t const* k = &i;
    int32_t l = 21;
    int32_t* const m = &l;
    return (0);
}
