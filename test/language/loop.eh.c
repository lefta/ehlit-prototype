#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

void EF12do_something(void)
{
}

int32_t main(void)
{
    int32_t i = 3;
    while (i)
    {
        EF12do_something();
        i = i - 1;
    }
    i = 3;
    while (i)
    {
        i = i - 1;
    }
    do
    {
        i++;
    } while (i < 10);
    do
    {
        EF12do_something();
        i--;
    } while (i > 0);
    for (i = 0; i < 5; i++)
    {
        EF12do_something();
        ++i;
    }
    for (int32_t j = 0, i = 10; i > 5 && j < 2; j++, i--, EF12do_something())
    {
        EF12do_something();
    }
    return (0);
}
