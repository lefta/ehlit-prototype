#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

enum EN8TestEnum
{
    EN8TestEnum4val1,
    EN8TestEnum4val2,
    EN8TestEnum4val3
};

enum EN12forward_decl;

void EF3funN8TestEnum(enum EN8TestEnum e)
{
}

enum EN8TestEnum* EF8enum_funrN8TestEnum(enum EN8TestEnum* s)
{
    return (s);
}

void* EF7any_funB3any(void* p)
{
    return (p);
}

int32_t main(void)
{
    enum EN8TestEnum e = EN8TestEnum4val1;
    EF3funN8TestEnum(e);
    enum EN8TestEnum* re = &e;
    *re = EN8TestEnum4val2;
    EF3funN8TestEnum(*re);
    re = EF8enum_funrN8TestEnum(&e);
    size_t ss = sizeof(enum EN8TestEnum);
    ss = sizeof(enum EN8TestEnum*);
    enum EN8TestEnum*(* psf)(enum EN8TestEnum*) = &EF8enum_funrN8TestEnum;
    re = (enum EN8TestEnum*)EF7any_funB3any(re);
    e = *(enum EN8TestEnum*)EF7any_funB3any(&e);
    re = ((enum EN8TestEnum*)0);
    return (0);
}
