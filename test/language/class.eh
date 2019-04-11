void use_class(ref test_class cls)

class test_class {
  int field1
  str field2
  ref int[] field3

  ctor() {}

  void set_fields(int f1, str f2, ref int[] f3) {
    field1 = f1
    field2 = f2
    ref field3 = f3
  }

  void this_test() {
    cls_fun(this)
    ref_cls_fun(this)
    ref_ref_cls_fun(this)
    any_fun(this)
  }
}

class forward_decl

void cls_fun(test_class cls)
void ref_cls_fun(ref test_class cls)
void ref_ref_cls_fun(ref ref test_class cls)

void fun(ref int i) {}
ref test_class class_fun(ref test_class cls) {
  return cls
}
any any_fun(any p) {
  return p
}

int main() {
  test_class cls
  cls.field1 = 0
  cls.field2 = "123456"
  ref cls.field3 = null
  fun(cls.field1)
  cls.set_fields(42, "Hello", null)

  ref test_class rcls = cls
  rcls.field1 = 0
  rcls.field2 = "123456"
  ref rcls.field3 = null
  fun(rcls.field1)
  rcls.set_fields(42, "Hello", null)

  ref rcls = class_fun(cls)
  size ss = sizeof(test_class)
  ss = sizeof(ref test_class)
  func<ref test_class(ref test_class)> psf = class_fun
  ref rcls = any_fun(rcls)
  cls = any_fun(cls)
  ref rcls = ref test_class(0)

  return 0
}

class ctor_args {
  int foo

  ctor(int i, str s) {}
}

void ctor_cls_fun(ctor_args cls)
void ref_ctor_cls_fun(ref ctor_args cls)
