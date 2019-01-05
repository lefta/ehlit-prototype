enum TestEnum {
  val1
  val2
  val3
}

enum forward_decl

void fun(TestEnum e) {}
ref TestEnum enum_fun(ref TestEnum s) {
  return s
}
any any_fun(any p) {
  return p
}

int main() {
  TestEnum e = TestEnum.val1
  fun(e)

  ref TestEnum re = e
  re = TestEnum.val2
  fun(re)

  ref re = enum_fun(e)
  size ss = sizeof(TestEnum)
  ss = sizeof(ref TestEnum)
  func<ref TestEnum(ref TestEnum)> psf = enum_fun
  ref re = any_fun(re)
  e = any_fun(e)
  ref re = ref TestEnum(0)

  return 0
}
