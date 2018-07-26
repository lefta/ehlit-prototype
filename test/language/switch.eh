int main(int ac, str[] av) {
  int res
  switch ac {
  case 1
    res = 0
  case 2
  case 3
    res = 1
  case 4 {
    res = 2
  }
  case 5
  case 6 {
    res = 3
  }
  case 7
    res = 4
    fallthrough
  case 8 {
    res = 5
    fallthrough
  }
  default
    res = 2
  }
  return 0
}
