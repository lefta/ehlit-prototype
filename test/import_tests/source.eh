struct forward_decl_struct
struct test_struct {
	int i
	str s
}

union forward_decl_union
union test_union {
	int i
	str s
}

enum forward_decl_enum
enum test_enum {
	val1
	val2
}

int fun_proto()
int fun_proto_args(int i, str s)

int fun() {
	return 5
}

int fun_proto_args(int i, str s) {
	if i < 5
		s = "bla"
	else
		s = "blabla"
}

alias int nb
func<nb()> fun_proto_ref = fun_proto

bool global = true
priv bool this_var_exported = false

nb main() {}

inline int inlined_function(int a, int b) {
	return a + b
}

priv int mul(int a, int b) {
	return a * b
}

priv inline int div(int a, int b) {
	return a / b
}
