#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

int32_t main(void)
{
    int32_t i = 0;
    int32_t j = 1;
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
    if (i)
    {
        ++i;
    }
    if (i++)
    {
        i;
    }
    int32_t* ri = 0;
    (*ri)++;
    (*ri)--;
    if (i == 1 && i == 2)
    {
        return (8);
    }
    if (i == 1 && i == 2 && i == 3 && i == 4)
    {
        return (9);
    }
    if (i != 1 && i != 2)
    {
        return (10);
    }
    if (i != 1 && i != 2 && i != 3 && i != 4)
    {
        return (11);
    }
    if (1 < i && i < 10)
    {
        return (12);
    }
    if (1 > i && i > 10)
    {
        return (13);
    }
    if (1 <= i && i <= 10)
    {
        return (14);
    }
    if (1 >= i && i >= 10)
    {
        return (15);
    }
    if (1 < i && i <= 10)
    {
        return (16);
    }
    if (1 > i && i >= 10)
    {
        return (17);
    }
    if (1 <= i && i < 10)
    {
        return (18);
    }
    if (1 >= i && i > 10)
    {
        return (19);
    }
    if (i && j)
    {
        return (1);
    }
    if (i || j)
    {
        return (2);
    }
    int32_t k = i << 5;
    k = i << j;
    k = 5 << j;
    k = i >> 5;
    k = i >> j;
    k = 5 >> j;
    k = ~k;
    if (i | j)
    {
        return (1);
    }
    if (i & j)
    {
        return (2);
    }
    if (i ^ j)
    {
        return (3);
    }
    k >>= i;
    k <<= i;
    k |= i;
    k &= i;
    k ^= i;
    return (0);
}
