#include <stddef.h>
#include <stdint.h>

void want_int(int32_t n)
{
}

int32_t main(int32_t ac, char** av)
{
    want_int(((int32_t)&av));
    void* test = ((char*)ac);
    size_t i = ((size_t*)av)[0];
    int8_t c = ((char*)ac)[0];
    return (0);
}
