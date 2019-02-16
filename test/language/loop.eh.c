#include <stddef.h>
#include <stdint.h>

void _EF12do_something(void)
{
}

int32_t main(void)
{
    int32_t i = 3;
    while (i)
    {
        _EF12do_something();
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
        _EF12do_something();
        i--;
    } while (i > 0);
    for (i = 0; i < 5; i++)
    {
        _EF12do_something();
        ++i;
    }
    for (int32_t j = 0, i = 10; i > 5 && j < 2; j++, i--, _EF12do_something())
    {
        _EF12do_something();
    }
    return (0);
}
