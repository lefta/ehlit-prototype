void non_namespaced_function()

namespace Foo {
    int some_variable = 42
    void some_function() {
        non_namespaced_function()
    }
}

namespace Bar.Nested {
    void some_nested_function() {
        Foo.some_function()
    }
}

namespace Bar {
    namespace Nested {
        void another_nested_function() {
            some_nested_function()
        }
    }
}

int main() {
    int var = Foo.some_variable
    Foo.some_function()
    Bar.Nested.some_nested_function()
    Bar.Nested.another_nested_function()
    return 0
}
