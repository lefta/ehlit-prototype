int main(int ac, str[] av) {
  int res
  switch ac {
  case 1
    res = 0
  case 2, 3
    res = 1
  case 7
    res = 4
    fallthrough
  default
    res = 2
  }
  return 0
}
