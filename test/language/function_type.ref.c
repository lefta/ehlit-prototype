#include <stddef.h>
#include <stdint.h>

void fun1(void)
{
}

int32_t fun2(int32_t i)
{
}

int32_t fun3(int32_t i, int32_t j)
{
}

int32_t** fun4(int32_t** arr)
{
}

int32_t main(void)
{
    void(* pfn1)() = &fun1;
    int32_t(* pfn2)(int32_t) = &fun2;
    int32_t(* pfn3)(int32_t, int32_t) = &fun3;
    int32_t**(* pfn4)(int32_t**) = &fun4;
    pfn1();
    pfn2(0);
    pfn3(0, 0);
    pfn4(NULL);
    return (0);
}
