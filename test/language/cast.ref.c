#include <stdio.h>

int main(int ac, char** av)
{
    printf("%d\n", ((int)&av));
    void* test = ((char*)ac);
    ((char*)test) = av[0];
    return (0);
}
