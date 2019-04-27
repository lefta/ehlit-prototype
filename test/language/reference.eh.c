#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

int32_t EF7set_intrB3int(int32_t* i)
{
    *i = 42;
    return (*i);
}

int32_t* EF10set_int_torB3intrB3int(int32_t* i, int32_t* j)
{
    *i = *j;
    return (i);
}

int32_t* EF11set_int_refrB3intrB3int(int32_t* i, int32_t* j)
{
    i = j;
    return (i);
}

int32_t** EF15set_int_ref_refrrB3intrrB3int(int32_t** i, int32_t** j)
{
    i = j;
    return (i);
}

void EF15set_int_ref_lv2rrB3intrrB3int(int32_t** i, int32_t** j)
{
    *i = *j;
}

int32_t main(void)
{
    int32_t i;
    int32_t* j = 21;
    i = EF7set_intrB3int(&i);
    j = EF10set_int_torB3intrB3int(&i, j);
    *j = *EF11set_int_refrB3intrB3int(&i, j);
    int32_t** k = &j;
    **k = 42;
    *k = j;
    k = EF15set_int_ref_refrrB3intrrB3int(&j, k);
    return (0);
}
