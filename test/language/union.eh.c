#include <stddef.h>
#include <stdint.h>

union _EU10test_union
{
    int32_t field1;
    char* field2;
    int32_t** field3;
};

union _EU12forward_decl;

void _EF3funRB3int(int32_t* i)
{
}

union _EU10test_union* _EF9union_funRU10test_union(union _EU10test_union* s)
{
    return (s);
}

void* _EF7any_funB3any(void* p)
{
    return (p);
}

int32_t main(void)
{
    union _EU10test_union t;
    t.field1 = 0;
    t.field2 = "123456";
    t.field3 = NULL;
    _EF3funRB3int(&t.field1);
    union _EU10test_union* rt = &t;
    rt->field1 = 0;
    rt->field2 = "123456";
    rt->field3 = NULL;
    _EF3funRB3int(&rt->field1);
    rt = _EF9union_funRU10test_union(&t);
    size_t ss = sizeof(union _EU10test_union);
    ss = sizeof(union _EU10test_union*);
    union _EU10test_union*(* psf)(union _EU10test_union*) = &_EF9union_funRU10test_union;
    rt = (union _EU10test_union*)_EF7any_funB3any(rt);
    t = *(union _EU10test_union*)_EF7any_funB3any(&t);
    rt = ((union _EU10test_union*)0);
    return (0);
}
