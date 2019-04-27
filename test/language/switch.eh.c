#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

int32_t main(int32_t ac, char** av)
{
    int32_t res;
    switch (ac)
    {
    case 1:
    {
        res = 0;
        break;
    }
    case 2:
    case 3:
    {
        res = 1;
        break;
    }
    case 7:
    {
        res = 4;
    }
    default:
    {
        res = 2;
        break;
    }
    }
    return (0);
}
