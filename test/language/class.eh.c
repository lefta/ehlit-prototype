#include <stddef.h>
#include <stdint.h>

struct _EC10test_class;
void _EF9use_classRC10test_class(struct _EC10test_class* cls);

struct _EC10test_class
{
    int32_t field1;
    char* field2;
    int32_t** field3;
};

void _EC10test_classF10set_fieldsB3intB3strRAB3int(struct _EC10test_class* this, int32_t f1, char* f2, int32_t** f3)
{
    this->field1 = f1;
    this->field2 = f2;
    this->field3 = f3;
}

void _EF7cls_funC10test_class(struct _EC10test_class cls);
void _EF11ref_cls_funRC10test_class(struct _EC10test_class* cls);
void _EF15ref_ref_cls_funRRC10test_class(struct _EC10test_class** cls);
void* _EF7any_funB3any(void* p);

void _EC10test_classF9this_test(struct _EC10test_class* this)
{
    _EF7cls_funC10test_class(*this);
    _EF11ref_cls_funRC10test_class(this);
    _EF15ref_ref_cls_funRRC10test_class(&this);
    _EF7any_funB3any(this);
}

struct _EC12forward_decl;
void _EF7cls_funC10test_class(struct _EC10test_class cls);
void _EF11ref_cls_funRC10test_class(struct _EC10test_class* cls);
void _EF15ref_ref_cls_funRRC10test_class(struct _EC10test_class** cls);

void _EF3funRB3int(int32_t* i)
{
}

struct _EC10test_class* _EF9class_funRC10test_class(struct _EC10test_class* cls)
{
    return (cls);
}

void* _EF7any_funB3any(void* p)
{
    return (p);
}

int32_t main(void)
{
    struct _EC10test_class cls;
    cls.field1 = 0;
    cls.field2 = "123456";
    cls.field3 = NULL;
    _EF3funRB3int(&cls.field1);
    _EC10test_classF10set_fieldsB3intB3strRAB3int(&cls, 42, "Hello", NULL);
    struct _EC10test_class* rcls = &cls;
    rcls->field1 = 0;
    rcls->field2 = "123456";
    rcls->field3 = NULL;
    _EF3funRB3int(&rcls->field1);
    _EC10test_classF10set_fieldsB3intB3strRAB3int(rcls, 42, "Hello", NULL);
    rcls = _EF9class_funRC10test_class(&cls);
    size_t ss = sizeof(struct _EC10test_class);
    ss = sizeof(struct _EC10test_class*);
    struct _EC10test_class*(* psf)(struct _EC10test_class*) = &_EF9class_funRC10test_class;
    rcls = (struct _EC10test_class*)_EF7any_funB3any(rcls);
    cls = *(struct _EC10test_class*)_EF7any_funB3any(&cls);
    rcls = ((struct _EC10test_class*)0);
    return (0);
}
