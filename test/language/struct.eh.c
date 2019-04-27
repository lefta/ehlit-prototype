#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

struct ES11test_struct;

void EF10use_structrS11test_struct(struct ES11test_struct* s);

struct ES11test_struct
{
    int32_t field1;
    char* field2;
    int32_t** field3;
};

struct ES12forward_decl;

void EF3funrB3int(int32_t* i)
{
}

struct ES11test_struct* EF10struct_funrS11test_struct(struct ES11test_struct* s)
{
    return (s);
}

void* EF7any_funB3any(void* p)
{
    return (p);
}

int32_t main(void)
{
    struct ES11test_struct t;
    t.field1 = 0;
    t.field2 = "123456";
    t.field3 = NULL;
    EF3funrB3int(&t.field1);
    struct ES11test_struct* rt = &t;
    rt->field1 = 0;
    rt->field2 = "123456";
    rt->field3 = NULL;
    EF3funrB3int(&rt->field1);
    rt = EF10struct_funrS11test_struct(&t);
    size_t ss = sizeof(struct ES11test_struct);
    ss = sizeof(struct ES11test_struct*);
    struct ES11test_struct*(* psf)(struct ES11test_struct*) = &EF10struct_funrS11test_struct;
    rt = (struct ES11test_struct*)EF7any_funB3any(rt);
    t = *(struct ES11test_struct*)EF7any_funB3any(&t);
    rt = ((struct ES11test_struct*)0);
    return (0);
}
