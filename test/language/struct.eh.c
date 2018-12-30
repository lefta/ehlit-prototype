#include <stddef.h>
#include <stdint.h>

struct _ES11test_struct
{
    int32_t field1;
    char* field2;
    int32_t** field3;
};

struct _ES12forward_decl;

void _EF3funRB3int(int32_t* i)
{
}

struct _ES11test_struct* _EF10struct_funRS11test_struct(struct _ES11test_struct* s)
{
    return (s);
}

void* _EF7any_funB3any(void* p)
{
    return (p);
}

int32_t main(void)
{
    struct _ES11test_struct t;
    t.field1 = 0;
    t.field2 = "123456";
    t.field3 = NULL;
    _EF3funRB3int(&t.field1);
    struct _ES11test_struct* rt = &t;
    rt->field1 = 0;
    rt->field2 = "123456";
    rt->field3 = NULL;
    _EF3funRB3int(&rt->field1);
    rt = _EF10struct_funRS11test_struct(&t);
    size_t ss = sizeof(struct _ES11test_struct);
    ss = sizeof(struct _ES11test_struct*);
    struct _ES11test_struct*(* psf)(struct _ES11test_struct*) = &_EF10struct_funRS11test_struct;
    rt = (struct _ES11test_struct*)_EF7any_funB3any(rt);
    t = *(struct _ES11test_struct*)_EF7any_funB3any(&t);
    rt = ((struct _ES11test_struct*)0);
    return (0);
}
