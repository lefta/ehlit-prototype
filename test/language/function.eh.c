#include <stddef.h>
#include <stdint.h>

void simple_fn(int32_t i)
{
}

void simple_fn_str(char* s)
{
}

int32_t* ref_call(void)
{
    return (NULL);
}

void inc(int32_t* nb)
{
    if (!nb)
    {
        return;
    }
    *nb += 1;
}

void inner_parens(int32_t i)
{
    if (!0)
    {
        i = 1;
        if (!0)
        {
            i = 2;
        }
        if (0)
        {
            i = 2;
        }
        i = 3;
    }
    i = 4;
    if (0)
    {
        i = 5;
    }
}

void func_with_default_params(int32_t par1, int32_t par2)
{
}

void func_with_trailing_comma(int32_t arg)
{
}

void declared_later(void);

int32_t main(int32_t ac, char** av)
{
    simple_fn(42);
    simple_fn(4 * 8);
    simple_fn_str("Hello, world!\n");
    ref_call();
    func_with_default_params(1, 2);
    func_with_default_params(3, 0);
    func_with_trailing_comma(4);
    declared_later();
    return (0);
}

void declared_later(void)
{
}

static void private_function(void)
{
}

inline void inline_function(void)
{
}

inline static int32_t inline_and_private_function(int32_t a, int32_t b)
{
    return (a + b);
}

void vargs_any_implicit(int32_t vargs_len, void** vargs)
{
    int32_t vlen = vargs_len;
    void* va1 = vargs[1];
}

void vargs_any_explicit(int32_t vargs_len, void** vargs)
{
}

void vargs_type(int32_t vargs_len, int32_t* vargs)
{
}

void vargs_complex_type(int32_t vargs_len, int32_t** vargs)
{
}

void args1_vargs_implicit(int32_t* i, int32_t vargs_len, void** vargs)
{
}

void args1_vargs_explicit(int32_t* i, int32_t vargs_len, int32_t* vargs)
{
}

void args3_vargs_implicit(char* s, int32_t i, int32_t* ri, int32_t vargs_len, void** vargs)
{
}

void args3_vargs_explicit(char* s, int32_t i, int32_t* ri, int32_t vargs_len, int32_t* vargs)
{
}

void call_vargs(void)
{
    void* __gen_fun_1[0] = {  };
    vargs_any_explicit(0, __gen_fun_1);
    void* __gen_fun_2[1] = { NULL };
    vargs_any_explicit(1, __gen_fun_2);
    void* __gen_fun_3[3] = { NULL, NULL, NULL };
    vargs_any_explicit(3, __gen_fun_3);
    int32_t i;
    int32_t __gen_fun_4[0] = {  };
    vargs_type(0, __gen_fun_4);
    int32_t __gen_fun_5[1] = { i };
    vargs_type(1, __gen_fun_5);
    int32_t __gen_fun_6[3] = { i, i, i };
    vargs_type(3, __gen_fun_6);
    int32_t* __gen_fun_7[2] = { &i, &i };
    vargs_complex_type(2, __gen_fun_7);
    int32_t __gen_fun_8[2] = { i, i };
    args3_vargs_explicit("Hello", i, &i, 2, __gen_fun_8);
}
