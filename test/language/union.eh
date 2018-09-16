union test_union {
  int field1
  str field2
  ref int[] field3
}

union forward_decl

void fun(ref int i) {}
ref test_union union_fun(ref test_union s) {
  return s
}
any any_fun(any p) {
  return p
}

int main() {
  test_union t
  t.field1 = 0
  t.field2 = "123456"
  ref t.field3 = null
  fun(t.field1)

  ref test_union rt = t
  rt.field1 = 0
  rt.field2 = "123456"
  ref rt.field3 = null
  fun(rt.field1)

  ref rt = union_fun(t)
  size ss = sizeof(test_union)
  ss = sizeof(ref test_union)
  func<ref test_union(ref test_union)> psf = union_fun
  ref rt = any_fun(rt)
  t = any_fun(t)
  ref rt = ref test_union(0)

  return 0
}
