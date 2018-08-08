void simple_fn(int i) {}
void simple_fn_str(str s) {}

ref int ref_call() {
	return null
}

void inc(ref int nb) {
	if !ref nb
		return
	nb += 1
}

void inner_parens(int i) {
	if true {
		i = 1
		if true {
			i = 2
		}
		if false {
			i = 2
		}
		i = 3
	}
	i = 4

	if false {
		i = 5
	}
}

void func_with_default_params(int par1, int par2 = 0) {}
void func_with_trailing_comma(int arg,) {}

int main(int ac, str[] av)
{
	simple_fn(42)
	simple_fn(4 * 8)
	simple_fn_str("Hello, world!\n")
	ref_call()
	func_with_default_params(1, 2)
	func_with_default_params(3)
	func_with_trailing_comma(4,)
	declared_later()
	return 0
}

void declared_later() {}
