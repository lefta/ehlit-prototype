#include <stddef.h>
#include <stdint.h>

int32_t main(void)
{
    int32_t i = 2;
    if (i == 2)
    {
        i = 3;
    }
    else if (i == 3)
    {
        i = 4;
    }
    else
    {
        i = 5;
    }
    return (0);
}
