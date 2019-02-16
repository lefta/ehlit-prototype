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
    return (0);
}
