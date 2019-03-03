#include <stddef.h>
#include <stdint.h>
void _EF23non_namespaced_function(void);
int32_t _EN3FooV13some_variable = 42;

void _EN3FooF13some_function(void)
{
    _EF23non_namespaced_function();
}

void _EN3BarN6NestedF20some_nested_function(void)
{
    _EN3FooF13some_function();
}

void _EN3BarN6NestedF23another_nested_function(void)
{
    _EN3BarN6NestedF20some_nested_function();
}

int32_t main(void)
{
    int32_t var = _EN3FooV13some_variable;
    _EN3FooF13some_function();
    _EN3BarN6NestedF20some_nested_function();
    _EN3BarN6NestedF23another_nested_function();
    return (0);
}
