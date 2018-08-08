#include <stddef.h>
#include <stdint.h>

void do_something(void)
{
}

int32_t main(void)
{
    int32_t i = 3;
    while (i)
    {
        do_something();
        i = i - 1;
    }
    i = 3;
    while (i)
    {
        i = i - 1;
    }
    return (0);
}
