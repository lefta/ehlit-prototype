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

int32_t** set_int_ref_ref(int32_t** i, int32_t** j)
{
    i = j;
    return (i);
}

void set_int_ref_lv2(int32_t** i, int32_t** j)
{
    *i = *j;
}

int32_t main(void)
{
    int32_t i;
    int32_t* j = 21;
    i = set_int(&i);
    j = set_int_to(&i, j);
    *j = *set_int_ref(&i, j);
    int32_t** k = &j;
    **k = 42;
    *k = j;
    k = set_int_ref_ref(&j, k);
    return (0);
}
