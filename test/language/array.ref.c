#include <stddef.h>
#include <stdio.h>

int main(int ac, char** av)
{
    char** av2 = av;
    while (ac)
    {
        ac--;
        av2[ac] = av[ac];
        puts(av[ac]);
    }
    return (0);
}
