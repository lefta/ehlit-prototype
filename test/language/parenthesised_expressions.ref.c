#include <stddef.h>
#include <stdint.h>

int32_t main(void)
{
    int32_t i = 42 + (4 * 2);
    i = (42 + 4) * 2;
    i = (42 + 4 * 2);
    i = (42) + (4) * (2);
    return (0);
}
