#include <stddef.h>
#include <stdint.h>

int32_t _EF3funB3intrB3int(int32_t i, int32_t* j);

void _EF6callerB3int(int32_t i)
{
    _EF3funB3intrB3int(i, &i);
}

int32_t _EF3funB3intrB3int(int32_t i, int32_t* j)
{
    return (*j);
}

int32_t* _EF7ref_funrB3int(int32_t* i)
{
    return (i);
}

int32_t main(void)
{
    int32_t i;
    int32_t* j;
    j = &i;
    *j = i;
    *j = _EF3funB3intrB3int(i, j);
    *j = _EF3funB3intrB3int(*j, &i);
    _EF3funB3intrB3int(i, j);
    i = *_EF7ref_funrB3int(&i);
    *j = *_EF7ref_funrB3int(j);
    j = _EF7ref_funrB3int(j);
    i = *((int32_t*)42);
    j = ((int32_t*)42);
    return (*j);
}
