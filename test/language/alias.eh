alias int nb
alias void nothing

nothing inc(ref int number) {
  if !ref number
    return
  number += 1
}

void do_nothing(nb n) {}

nb main() {
  alias do_nothing dn
  nb i = 42
  inc(i)
  dn(i)
  return i
}
