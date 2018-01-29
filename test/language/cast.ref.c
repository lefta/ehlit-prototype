#include <stdio.h>

int main(int ac, char** av)
{
    printf("%d\n", ((int)&av));
    void* test = ((char*)ac);
    ((char*)test) = av[0];
    char n = 0;
    ((char*)test)[0] = n;
    return (0);
}
