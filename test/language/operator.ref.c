#include <stddef.h>
#include <stdint.h>

int32_t main(void)
{
    int32_t i = 0;
    i = i + 5;
    i = i - 3;
    i = i * 4;
    i = i / 3;
    i = i % 3;
    i += 4;
    i -= 8;
    i *= 5;
    i /= 1;
    i %= 2;
    i--;
    i++;
    ++i;
    --i;
    if (i == 5)
    {
        return (1);
    }
    if (i != 5)
    {
        return (2);
    }
    if (i > 5)
    {
        return (3);
    }
    if (i < 5)
    {
        return (4);
    }
    if (i >= 5)
    {
        return (5);
    }
    if (i <= 5)
    {
        return (6);
    }
    if (!i)
    {
        return (7);
    }
    return (0);
}
