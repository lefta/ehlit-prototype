#include <stddef.h>
#include <stdint.h>

void _EF9simple_fnB3int(int32_t i)
{
}

void _EF13simple_fn_strB3str(char* s)
{
}

int32_t* _EF8ref_call(void)
{
    return (NULL);
}

void _EF3incrB3int(int32_t* nb)
{
    if (!nb)
    {
        return;
    }
    *nb += 1;
}

void _EF12inner_parensB3int(int32_t i)
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

void _EF24func_with_default_paramsB3intB3int(int32_t par1, int32_t par2)
{
}

void _EF24func_with_trailing_commaB3int(int32_t arg)
{
}

void _EF14declared_later(void);

int32_t main(int32_t ac, char** av)
{
    _EF9simple_fnB3int(42);
    _EF9simple_fnB3int(4 * 8);
    _EF13simple_fn_strB3str("Hello, world!\n");
    _EF8ref_call();
    _EF24func_with_default_paramsB3intB3int(1, 2);
    _EF24func_with_default_paramsB3intB3int(3, 0);
    _EF24func_with_trailing_commaB3int(4);
    _EF14declared_later();
    return (0);
}

void _EF14declared_later(void)
{
}

static void _EF16private_function(void)
{
}

inline void _EF15inline_function(void)
{
}

inline static int32_t _EF27inline_and_private_functionB3intB3int(int32_t a, int32_t b)
{
    return (a + b);
}

void _EF18vargs_any_implicitvB3any(int32_t _EB9vargs_len, void** _EB5vargs)
{
    int32_t vlen = _EB9vargs_len;
    void* va1 = _EB5vargs[1];
}

void _EF18vargs_any_explicitvB3any(int32_t _EB9vargs_len, void** _EB5vargs)
{
}

void _EF10vargs_typevB3int(int32_t _EB9vargs_len, int32_t* _EB5vargs)
{
}

void _EF18vargs_complex_typevrB3int(int32_t _EB9vargs_len, int32_t** _EB5vargs)
{
}

void _EF20args1_vargs_implicitrB3intvB3any(int32_t* i, int32_t _EB9vargs_len, void** _EB5vargs)
{
}

void _EF20args1_vargs_explicitrB3intvB3int(int32_t* i, int32_t _EB9vargs_len, int32_t* _EB5vargs)
{
}

void _EF20args3_vargs_implicitB3strB3intrB3intvB3any(char* s, int32_t i, int32_t* ri, int32_t _EB9vargs_len, void** _EB5vargs)
{
}

void _EF20args3_vargs_explicitB3strB3intrB3intvB3int(char* s, int32_t i, int32_t* ri, int32_t _EB9vargs_len, int32_t* _EB5vargs)
{
}

void _EF10call_vargs(void)
{
    void* __gen_fun_1[0] = {  };
    _EF18vargs_any_explicitvB3any(0, __gen_fun_1);
    void* __gen_fun_2[1] = { NULL };
    _EF18vargs_any_explicitvB3any(1, __gen_fun_2);
    void* __gen_fun_3[3] = { NULL, NULL, NULL };
    _EF18vargs_any_explicitvB3any(3, __gen_fun_3);
    int32_t i;
    int32_t __gen_fun_4[0] = {  };
    _EF10vargs_typevB3int(0, __gen_fun_4);
    int32_t __gen_fun_5[1] = { i };
    _EF10vargs_typevB3int(1, __gen_fun_5);
    int32_t __gen_fun_6[3] = { i, i, i };
    _EF10vargs_typevB3int(3, __gen_fun_6);
    int32_t* __gen_fun_7[2] = { &i, &i };
    _EF18vargs_complex_typevrB3int(2, __gen_fun_7);
    int32_t __gen_fun_8[2] = { i, i };
    _EF20args3_vargs_explicitB3strB3intrB3intvB3int("Hello", i, &i, 2, __gen_fun_8);
}
void cdecl_proto(void);

void cdecl_fun(void)
{
}

static void cdecl_priv_fun(void)
{
}

inline void cdecl_inl_fun(void)
{
}

inline static void cdecl_priv_inl_fun(void)
{
}
