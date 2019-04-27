#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

int32_t EF3funB3intrB3int(int32_t i, int32_t* j);

void EF6callerB3int(int32_t i)
{
    EF3funB3intrB3int(i, &i);
}

int32_t EF3funB3intrB3int(int32_t i, int32_t* j)
{
    return (*j);
}

int32_t* EF7ref_funrB3int(int32_t* i)
{
    return (i);
}

int32_t main(void)
{
    int32_t i;
    int32_t* j;
    j = &i;
    *j = i;
    *j = EF3funB3intrB3int(i, j);
    *j = EF3funB3intrB3int(*j, &i);
    EF3funB3intrB3int(i, j);
    i = *EF7ref_funrB3int(&i);
    *j = *EF7ref_funrB3int(j);
    j = EF7ref_funrB3int(j);
    i = *((int32_t*)42);
    j = ((int32_t*)42);
    return (*j);
}
