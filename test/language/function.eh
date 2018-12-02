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

priv void private_function() {}
inline void inline_function() {}
inline priv int inline_and_private_function(int a, int b) {
	return a + b
}

void vargs_any_implicit(...) {
	int vlen = vargs.length
	any va1 = vargs[1]
}

void vargs_any_explicit(any...) {}
void vargs_type(int...) {}
void vargs_complex_type(ref int...) {}
void args1_vargs_implicit(ref int i, ...) {}
void args1_vargs_explicit(ref int i, int...) {}
void args3_vargs_implicit(str s, int i, ref int ri, ...) {}
void args3_vargs_explicit(str s, int i, ref int ri, int...) {}

void call_vargs() {
	vargs_any_explicit()
	vargs_any_explicit(null)
	vargs_any_explicit(null, null, null)

	int i
	vargs_type()
	vargs_type(i)
	vargs_type(i, i, i)
	vargs_complex_type(i, i)
	args3_vargs_explicit("Hello", i, i, i, i)
}
