#include <stddef.h>
#include <stdint.h>

int32_t _EF7set_intRB3int(int32_t* i)
{
    *i = 42;
    return (*i);
}

int32_t* _EF10set_int_toRB3intRB3int(int32_t* i, int32_t* j)
{
    *i = *j;
    return (i);
}

int32_t* _EF11set_int_refRB3intRB3int(int32_t* i, int32_t* j)
{
    i = j;
    return (i);
}

int32_t** _EF15set_int_ref_refRRB3intRRB3int(int32_t** i, int32_t** j)
{
    i = j;
    return (i);
}

void _EF15set_int_ref_lv2RRB3intRRB3int(int32_t** i, int32_t** j)
{
    *i = *j;
}

int32_t main(void)
{
    int32_t i;
    int32_t* j = 21;
    i = _EF7set_intRB3int(&i);
    j = _EF10set_int_toRB3intRB3int(&i, j);
    *j = *_EF11set_int_refRB3intRB3int(&i, j);
    int32_t** k = &j;
    **k = 42;
    *k = j;
    k = _EF15set_int_ref_refRRB3intRRB3int(&j, k);
    return (0);
}
