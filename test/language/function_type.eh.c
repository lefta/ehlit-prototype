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

void fun5(int8_t* c)
{
}
void vfun1(int32_t i, int32_t vargs_len, int32_t* vargs);
void vfun2(int32_t vargs_len, int32_t** vargs);
void vfun3(int32_t i, int32_t vargs_len, void** vargs);
void vfun4(int32_t vargs_len, void** vargs);

int32_t main(void)
{
    void(* pfn1)() = &fun1;
    int32_t(* pfn2)(int32_t) = &fun2;
    int32_t(* pfn3)(int32_t, int32_t) = &fun3;
    int32_t**(* pfn4)(int32_t**) = &fun4;
    void(* pfn5)(int8_t*) = &fun5;
    void(* vpfn1)(int32_t, int32_t, int32_t*) = &vfun1;
    void(* vpfn2)(int32_t, int32_t**) = &vfun2;
    void(* vpfn3)(int32_t, int32_t, void**) = &vfun3;
    void(* vpfn4)(int32_t, void**) = &vfun4;
    pfn1();
    pfn2(0);
    int32_t i = pfn2(0);
    pfn3(0, 0);
    i = pfn3(0, 0);
    pfn4(NULL);
    int32_t** rai = pfn4(NULL);
    int32_t* ai = *pfn4(NULL);
    char* s = "123456";
    pfn5(&s[0]);
    return (0);
}
