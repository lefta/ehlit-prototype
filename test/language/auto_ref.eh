
int fun(int i, ref int j) {
  return j
}

ref int ref_fun(ref int i) {
  return i
}

int main() {
  int i
  ref int j

  ref j = ref i
  j = ref i

  j = ref fun(i, j)
  j = fun(j, i)
  fun(ref i, j)

  i = ref_fun(i)
  j = ref_fun(j)
  ref j = ref_fun(ref j)

  i = ref int(42)
  ref j = ref int(42)

  return ref j
}
