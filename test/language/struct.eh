void use_struct(ref test_struct s)

struct test_struct {
  int field1
  str field2
  ref int[] field3
}

struct forward_decl

void fun(ref int i) {}
ref test_struct struct_fun(ref test_struct s) {
  return s
}
any any_fun(any p) {
  return p
}

int main() {
  test_struct t
  t.field1 = 0
  t.field2 = "123456"
  ref t.field3 = null
  fun(t.field1)

  ref test_struct rt = t
  rt.field1 = 0
  rt.field2 = "123456"
  ref rt.field3 = null
  fun(rt.field1)

  ref rt = struct_fun(t)
  size ss = sizeof(test_struct)
  ss = sizeof(ref test_struct)
  func<ref test_struct(ref test_struct)> psf = struct_fun
  ref rt = any_fun(rt)
  t = any_fun(t)
  ref rt = cast<ref test_struct>(0)

  return 0
}
