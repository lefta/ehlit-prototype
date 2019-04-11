
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
int fun()
int fun_proto_args(int i, str s)
alias int nb
func<nb()> fun_proto_ref = fun_proto
bool global = true

nb main()
inline int inlined_function(int a, int b) {
    return a + b
}

namespace Foo {
    void namespaced_func()
    int namespaced_var
}

namespace Bar {

    namespace Nested {
        void nested_func()
    }
}

namespace Bar {

    namespace Nested {
        void second_nested_func()
    }
}

class A

class B {
    int property
    str name

    ctor(int some_arg)
    void method()
}
