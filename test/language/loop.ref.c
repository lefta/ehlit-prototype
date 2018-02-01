#include <stddef.h>
#include <stdio.h>

int main(void)
{
    int i = 3;
    while (i)
    {
        printf("looping\n");
        i = i - 1;
    }
    i = 3;
    while (i)
    {
        i = i - 1;
    }
    return (0);
}
