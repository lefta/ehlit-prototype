#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

int32_t set_int(int32_t* i)
{
    *i = 42;
    return (*i);
}

int32_t* set_int_to(int32_t* i, int32_t* j)
{
    *i = *j;
    return (i);
}

int32_t* set_int_ref(int32_t* i, int32_t* j)
{
    i = j;
    return (i);
}

int32_t main(void)
{
    int32_t i;
    int32_t* j = 21;
    i = set_int(&i);
    j = set_int_to(&i, j);
    *j = *set_int_ref(&i, j);
    return (0);
}
