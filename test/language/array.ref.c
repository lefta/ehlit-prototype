#include <stdio.h>

int main(int ac, char** av)
{
    while (ac)
    {
        ac--;
        puts(av[ac]);
    }
    return (0);
}
