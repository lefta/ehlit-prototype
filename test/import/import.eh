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

nb main() {}
