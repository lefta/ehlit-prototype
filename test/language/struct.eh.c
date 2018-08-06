#include <stddef.h>
#include <stdint.h>

struct test_struct
{
    int32_t field1;
    char* field2;
    int32_t** field3;
};

struct forward_decl;

void fun(int32_t* i)
{
}

struct test_struct* struct_fun(struct test_struct* s)
{
    return (s);
}

void* any_fun(void* p)
{
    return (p);
}

int32_t main(void)
{
    struct test_struct t;
    t.field1 = 0;
    t.field2 = "123456";
    t.field3 = NULL;
    fun(&t.field1);
    struct test_struct* rt = &t;
    rt->field1 = 0;
    rt->field2 = "123456";
    rt->field3 = NULL;
    fun(&rt->field1);
    rt = struct_fun(&t);
    size_t ss = sizeof(struct test_struct);
    ss = sizeof(struct test_struct*);
    struct test_struct*(* psf)(struct test_struct*) = &struct_fun;
    rt = (struct test_struct*)any_fun(rt);
    t = *(struct test_struct*)any_fun(&t);
    rt = ((struct test_struct*)0);
    return (0);
}
