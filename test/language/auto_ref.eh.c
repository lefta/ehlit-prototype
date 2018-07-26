#include <stddef.h>
#include <stdint.h>

int32_t fun(int32_t i, int32_t* j)
{
    return (*j);
}

int32_t* ref_fun(int32_t* i)
{
    return (i);
}

int32_t main(void)
{
    int32_t i;
    int32_t* j;
    j = &i;
    *j = i;
    *j = fun(i, j);
    *j = fun(*j, &i);
    fun(i, j);
    i = *ref_fun(&i);
    *j = *ref_fun(j);
    j = ref_fun(j);
    return (*j);
}
