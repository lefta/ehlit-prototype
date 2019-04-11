#include <stddef.h>
#include <stdint.h>

void _EF4fun1(void)
{
}

int32_t _EF4fun2B3int(int32_t i)
{
}

int32_t _EF4fun3B3intB3int(int32_t i, int32_t j)
{
}

int32_t** _EF4fun4rAB3int(int32_t** arr)
{
}

void _EF4fun5rB4char(int8_t* c)
{
}

void _EF5vfun1B3intvB3int(int32_t i, int32_t _EB9vargs_len, int32_t* _EB5vargs);

void _EF5vfun2vAB3int(int32_t _EB9vargs_len, int32_t** _EB5vargs);

void _EF5vfun3B3intvB3any(int32_t i, int32_t _EB9vargs_len, void** _EB5vargs);

void _EF5vfun4vB3any(int32_t _EB9vargs_len, void** _EB5vargs);

int32_t main(void)
{
    void(* pfn1)() = &_EF4fun1;
    int32_t(* pfn2)(int32_t) = &_EF4fun2B3int;
    int32_t(* pfn3)(int32_t, int32_t) = &_EF4fun3B3intB3int;
    int32_t**(* pfn4)(int32_t**) = &_EF4fun4rAB3int;
    void(* pfn5)(int8_t*) = &_EF4fun5rB4char;
    void(* vpfn1)(int32_t, int32_t, int32_t*) = &_EF5vfun1B3intvB3int;
    void(* vpfn2)(int32_t, int32_t**) = &_EF5vfun2vAB3int;
    void(* vpfn3)(int32_t, int32_t, void**) = &_EF5vfun3B3intvB3any;
    void(* vpfn4)(int32_t, void**) = &_EF5vfun4vB3any;
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
