#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
uint8_t EV6global = !0;
static int32_t EV16universal_answer = 42;
int32_t cdecl_var = 42;
static int32_t cdecl_priv_var = 42;
static int32_t priv_cdecl_var = 42;

int32_t main(void)
{
    static int32_t globint = 42;
    int32_t i = 42;
    int32_t j;
    j = 21;
    if (i / 2 == j)
    {
        int32_t k;
        k = 1;
    }
    EV6global = 0;
    EV16universal_answer = 12;
    globint = 12;
    cdecl_var = 12;
    cdecl_priv_var = 12;
    priv_cdecl_var = 12;
    return (0);
}
