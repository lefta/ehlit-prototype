#include <stddef.h>
#include <stdint.h>

union test_union
{
    int32_t field1;
    char* field2;
    int32_t** field3;
};

union forward_decl;

void fun(int32_t* i)
{
}

union test_union* union_fun(union test_union* s)
{
    return (s);
}

void* any_fun(void* p)
{
    return (p);
}

int32_t main(void)
{
    union test_union t;
    t.field1 = 0;
    t.field2 = "123456";
    t.field3 = NULL;
    fun(&t.field1);
    union test_union* rt = &t;
    rt->field1 = 0;
    rt->field2 = "123456";
    rt->field3 = NULL;
    fun(&rt->field1);
    rt = union_fun(&t);
    size_t ss = sizeof(union test_union);
    ss = sizeof(union test_union*);
    union test_union*(* psf)(union test_union*) = &union_fun;
    rt = (union test_union*)any_fun(rt);
    t = *(union test_union*)any_fun(&t);
    rt = ((union test_union*)0);
    return (0);
}
