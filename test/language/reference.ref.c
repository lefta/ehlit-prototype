#include <stdio.h>

void set_int(int* i)
{
    *i = 42;
}

void set_int_to(int* i, int* j)
{
    *i = *j;
}

void set_int_ref(int* i, int* j)
{
    i = j;
}

int main(void)
{
    int i;
    int j = 21;
    set_int(&i);
    set_int_to(&i, &j);
    set_int_ref(&i, &j);
    return (0);
}
