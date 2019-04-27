#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

enum _EN8TestEnum
{
    _EN8TestEnum4val1,
    _EN8TestEnum4val2,
    _EN8TestEnum4val3
};

enum _EN12forward_decl;

void _EF3funN8TestEnum(enum _EN8TestEnum e)
{
}

enum _EN8TestEnum* _EF8enum_funrN8TestEnum(enum _EN8TestEnum* s)
{
    return (s);
}

void* _EF7any_funB3any(void* p)
{
    return (p);
}

int32_t main(void)
{
    enum _EN8TestEnum e = _EN8TestEnum4val1;
    _EF3funN8TestEnum(e);
    enum _EN8TestEnum* re = &e;
    *re = _EN8TestEnum4val2;
    _EF3funN8TestEnum(*re);
    re = _EF8enum_funrN8TestEnum(&e);
    size_t ss = sizeof(enum _EN8TestEnum);
    ss = sizeof(enum _EN8TestEnum*);
    enum _EN8TestEnum*(* psf)(enum _EN8TestEnum*) = &_EF8enum_funrN8TestEnum;
    re = (enum _EN8TestEnum*)_EF7any_funB3any(re);
    e = *(enum _EN8TestEnum*)_EF7any_funB3any(&e);
    re = ((enum _EN8TestEnum*)0);
    return (0);
}
