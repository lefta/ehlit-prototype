#include <stdio.h>

int set_int(int* i)
{
    *i = 42;
    return (*i);
}

int* set_int_to(int* i, int* j)
{
    *i = *j;
    return (i);
}

int* set_int_ref(int* i, int* j)
{
    i = j;
    return (i);
}

int main(void)
{
    int i;
    int* j = 21;
    i = set_int(&i);
    j = set_int_to(&i, j);
    *j = *set_int_ref(&i, j);
    return (0);
}
