#include <stddef.h>
#include <stdint.h>

uint8_t not_true(uint8_t v)
{
    return (!v);
}

int32_t main(void)
{
    uint8_t b1 = !0;
    uint8_t b2 = 0;
    b1 = 0;
    b2 = !0;
    if (not_true(!0))
    {
        return (1);
    }
    return (0);
}
