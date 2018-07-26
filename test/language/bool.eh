bool not_true(bool v) {
  return !v
}

int main() {
  bool b1 = true
  bool b2 = false
  b1 = false
  b2 = true
  if not_true(true)
    return 1
  return 0
}
