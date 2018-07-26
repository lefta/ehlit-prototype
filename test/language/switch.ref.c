#include <stddef.h>
#include <stdint.h>

int32_t main(int32_t ac, char** av)
{
    int32_t res;
    switch (ac)
    {
    case 1:
        res = 0;
        break;
    case 2:
    case 3:
        res = 1;
        break;
    case 4:
    {
        res = 2;
        break;
    }
    case 5:
    case 6:
    {
        res = 3;
        break;
    }
    case 7:
        res = 4;
    case 8:
    {
        res = 5;
    }
    default:
        res = 2;
        break;
    }
    return (0);
}
