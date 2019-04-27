#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

void EF8want_intB3int(int32_t n)
{
}

int32_t main(int32_t ac, char** av)
{
    EF8want_intB3int(((int32_t)&av));
    void* test = ((char*)ac);
    size_t i = ((size_t*)av)[0];
    int8_t c = ((char*)ac)[0];
    char* s = "YOLO";
    char* string = ((char*)&s[1]);
    return (0);
}
