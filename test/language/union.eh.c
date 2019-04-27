#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

union EU10test_union;

void EF9use_unionrU10test_union(union EU10test_union* u);

union EU10test_union
{
    int32_t field1;
    char* field2;
    int32_t** field3;
};

union EU12forward_decl;

void EF3funrB3int(int32_t* i)
{
}

union EU10test_union* EF9union_funrU10test_union(union EU10test_union* s)
{
    return (s);
}

void* EF7any_funB3any(void* p)
{
    return (p);
}

int32_t main(void)
{
    union EU10test_union t;
    t.field1 = 0;
    t.field2 = "123456";
    t.field3 = NULL;
    EF3funrB3int(&t.field1);
    union EU10test_union* rt = &t;
    rt->field1 = 0;
    rt->field2 = "123456";
    rt->field3 = NULL;
    EF3funrB3int(&rt->field1);
    rt = EF9union_funrU10test_union(&t);
    size_t ss = sizeof(union EU10test_union);
    ss = sizeof(union EU10test_union*);
    union EU10test_union*(* psf)(union EU10test_union*) = &EF9union_funrU10test_union;
    rt = (union EU10test_union*)EF7any_funB3any(rt);
    t = *(union EU10test_union*)EF7any_funB3any(&t);
    rt = ((union EU10test_union*)0);
    return (0);
}
