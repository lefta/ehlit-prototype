#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

struct EC10test_class;

void EF9use_classrC10test_class(struct EC10test_class* cls);

struct EC10test_class
{
    int32_t field1;
    char* field2;
    int32_t** field3;
};

void EC10test_classI(struct EC10test_class* this)
{
}

void EC10test_classD(struct EC10test_class* this)
{
}

void EC10test_classF10set_fieldsB3intB3strraB3int(struct EC10test_class* this, int32_t f1, char* f2, int32_t** f3)
{
    this->field1 = f1;
    this->field2 = f2;
    this->field3 = f3;
}

void EF7cls_funC10test_class(struct EC10test_class cls);
void EF11ref_cls_funrC10test_class(struct EC10test_class* cls);
void EF15ref_ref_cls_funrrC10test_class(struct EC10test_class** cls);
void* EF7any_funB3any(void* p);

void EC10test_classF9this_test(struct EC10test_class* this)
{
    EF7cls_funC10test_class(*this);
    EF11ref_cls_funrC10test_class(this);
    EF15ref_ref_cls_funrrC10test_class(&this);
    EF7any_funB3any(this);
}

struct EC12forward_decl;

void EF7cls_funC10test_class(struct EC10test_class cls);

void EF11ref_cls_funrC10test_class(struct EC10test_class* cls);

void EF15ref_ref_cls_funrrC10test_class(struct EC10test_class** cls);

void EF3funrB3int(int32_t* i)
{
}

struct EC10test_class* EF9class_funrC10test_class(struct EC10test_class* cls)
{
    return (cls);
}

void* EF7any_funB3any(void* p)
{
    return (p);
}

int32_t main(void)
{
    struct EC10test_class cls;
    EC10test_classI(&cls);
    cls.field1 = 0;
    cls.field2 = "123456";
    cls.field3 = NULL;
    EF3funrB3int(&cls.field1);
    EC10test_classF10set_fieldsB3intB3strraB3int(&cls, 42, "Hello", NULL);
    struct EC10test_class* rcls = &cls;
    rcls->field1 = 0;
    rcls->field2 = "123456";
    rcls->field3 = NULL;
    EF3funrB3int(&rcls->field1);
    EC10test_classF10set_fieldsB3intB3strraB3int(rcls, 42, "Hello", NULL);
    rcls = EF9class_funrC10test_class(&cls);
    size_t ss = sizeof(struct EC10test_class);
    ss = sizeof(struct EC10test_class*);
    struct EC10test_class*(* psf)(struct EC10test_class*) = &EF9class_funrC10test_class;
    rcls = (struct EC10test_class*)EF7any_funB3any(rcls);
    cls = *(struct EC10test_class*)EF7any_funB3any(&cls);
    rcls = ((struct EC10test_class*)0);
    return (0);
}

struct EC9ctor_args
{
    int32_t foo;
};

void EC9ctor_argsIB3intB3str(struct EC9ctor_args* this, int32_t i, char* s)
{
}

void EC9ctor_argsD(struct EC9ctor_args* this)
{
}

void EF12ctor_cls_funC9ctor_args(struct EC9ctor_args cls);

void EF16ref_ctor_cls_funrC9ctor_args(struct EC9ctor_args* cls);

void EF15ctor_dtor_tests(void)
{
    struct EC10test_class cls;
    EC10test_classI(&cls);
    struct EC10test_class* rcls = &cls;
    struct EC9ctor_args cls2;
    EC9ctor_argsIB3intB3str(&cls2, 42, "Hello");
    struct EC9ctor_args* rcls2 = &cls2;
    rcls = malloc(sizeof(struct EC10test_class));
    EC10test_classI(rcls);
    rcls = malloc(sizeof(struct EC10test_class));
    EC10test_classI(rcls);
    rcls2 = malloc(sizeof(struct EC9ctor_args));
    EC9ctor_argsIB3intB3str(rcls2, 42, "Hello");
    struct EC10test_class __gen_fun_1;
    EC10test_classI(&__gen_fun_1);
    EF7cls_funC10test_class(__gen_fun_1);
    struct EC10test_class __gen_fun_2;
    EC10test_classI(&__gen_fun_2);
    EF11ref_cls_funrC10test_class(&__gen_fun_2);
    struct EC9ctor_args __gen_fun_3;
    EC9ctor_argsIB3intB3str(&__gen_fun_3, 42, "Hello");
    EF12ctor_cls_funC9ctor_args(__gen_fun_3);
    struct EC9ctor_args __gen_fun_4;
    EC9ctor_argsIB3intB3str(&__gen_fun_4, 42, "Hello");
    EF16ref_ctor_cls_funrC9ctor_args(&__gen_fun_4);
    struct EC9ctor_args* __gen_fun_5 = malloc(sizeof(struct EC9ctor_args));
    EC9ctor_argsIB3intB3str(__gen_fun_5, 42, "Hello");
    EF16ref_ctor_cls_funrC9ctor_args(__gen_fun_5);
}
