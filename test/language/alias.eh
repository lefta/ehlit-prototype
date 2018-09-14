alias int nb
alias void nothing
alias func<void(nb)> pfn

nothing inc(ref int number) {
  if !ref number
    return
  number += 1
}

void do_nothing(nb n) {}

nb main() {
  alias do_nothing dn
  nb i = 42
  pfn pdn = dn
  inc(i)
  dn(i)
  pdn(i)
  return i
}
