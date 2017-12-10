#include <stdio.h>

int main(int ac, char** av)
{
    printf("%d\n", ((int)&av));
    char* test = ((char*)ac);
    return (0);
}
