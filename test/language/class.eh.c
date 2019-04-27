#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

struct _EC10test_class;

void _EF9use_classrC10test_class(struct _EC10test_class* cls);

struct _EC10test_class
{
    int32_t field1;
    char* field2;
    int32_t** field3;
};

void _EC10test_classI(struct _EC10test_class* this)
{
}

void _EC10test_classF10set_fieldsB3intB3strraB3int(struct _EC10test_class* this, int32_t f1, char* f2, int32_t** f3)
{
    this->field1 = f1;
    this->field2 = f2;
    this->field3 = f3;
}

void _EF7cls_funC10test_class(struct _EC10test_class cls);
void _EF11ref_cls_funrC10test_class(struct _EC10test_class* cls);
void _EF15ref_ref_cls_funrrC10test_class(struct _EC10test_class** cls);
void* _EF7any_funB3any(void* p);

void _EC10test_classF9this_test(struct _EC10test_class* this)
{
    _EF7cls_funC10test_class(*this);
    _EF11ref_cls_funrC10test_class(this);
    _EF15ref_ref_cls_funrrC10test_class(&this);
    _EF7any_funB3any(this);
}

struct _EC12forward_decl;

void _EF7cls_funC10test_class(struct _EC10test_class cls);

void _EF11ref_cls_funrC10test_class(struct _EC10test_class* cls);

void _EF15ref_ref_cls_funrrC10test_class(struct _EC10test_class** cls);

void _EF3funrB3int(int32_t* i)
{
}

struct _EC10test_class* _EF9class_funrC10test_class(struct _EC10test_class* cls)
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
    _EC10test_classI(&cls);
    cls.field1 = 0;
    cls.field2 = "123456";
    cls.field3 = NULL;
    _EF3funrB3int(&cls.field1);
    _EC10test_classF10set_fieldsB3intB3strraB3int(&cls, 42, "Hello", NULL);
    struct _EC10test_class* rcls = &cls;
    rcls->field1 = 0;
    rcls->field2 = "123456";
    rcls->field3 = NULL;
    _EF3funrB3int(&rcls->field1);
    _EC10test_classF10set_fieldsB3intB3strraB3int(rcls, 42, "Hello", NULL);
    rcls = _EF9class_funrC10test_class(&cls);
    size_t ss = sizeof(struct _EC10test_class);
    ss = sizeof(struct _EC10test_class*);
    struct _EC10test_class*(* psf)(struct _EC10test_class*) = &_EF9class_funrC10test_class;
    rcls = (struct _EC10test_class*)_EF7any_funB3any(rcls);
    cls = *(struct _EC10test_class*)_EF7any_funB3any(&cls);
    rcls = ((struct _EC10test_class*)0);
    return (0);
}

struct _EC9ctor_args
{
    int32_t foo;
};

void _EC9ctor_argsIB3intB3str(struct _EC9ctor_args* this, int32_t i, char* s)
{
}

void _EF12ctor_cls_funC9ctor_args(struct _EC9ctor_args cls);

void _EF16ref_ctor_cls_funrC9ctor_args(struct _EC9ctor_args* cls);

void _EF15ctor_dtor_tests(void)
{
    struct _EC10test_class cls;
    _EC10test_classI(&cls);
    struct _EC10test_class* rcls = &cls;
    struct _EC9ctor_args cls2;
    _EC9ctor_argsIB3intB3str(&cls2, 42, "Hello");
    struct _EC9ctor_args* rcls2 = &cls2;
    rcls = malloc(sizeof(struct _EC10test_class));
    _EC10test_classI(rcls);
    rcls = malloc(sizeof(struct _EC10test_class));
    _EC10test_classI(rcls);
    rcls2 = malloc(sizeof(struct _EC9ctor_args));
    _EC9ctor_argsIB3intB3str(rcls2, 42, "Hello");
    struct _EC10test_class __gen_fun_1;
    _EC10test_classI(&__gen_fun_1);
    _EF7cls_funC10test_class(__gen_fun_1);
    struct _EC10test_class __gen_fun_2;
    _EC10test_classI(&__gen_fun_2);
    _EF11ref_cls_funrC10test_class(&__gen_fun_2);
    struct _EC9ctor_args __gen_fun_3;
    _EC9ctor_argsIB3intB3str(&__gen_fun_3, 42, "Hello");
    _EF12ctor_cls_funC9ctor_args(__gen_fun_3);
    struct _EC9ctor_args __gen_fun_4;
    _EC9ctor_argsIB3intB3str(&__gen_fun_4, 42, "Hello");
    _EF16ref_ctor_cls_funrC9ctor_args(&__gen_fun_4);
    struct _EC9ctor_args* __gen_fun_5 = malloc(sizeof(struct _EC9ctor_args));
    _EC9ctor_argsIB3intB3str(__gen_fun_5, 42, "Hello");
    _EF16ref_ctor_cls_funrC9ctor_args(__gen_fun_5);
}
