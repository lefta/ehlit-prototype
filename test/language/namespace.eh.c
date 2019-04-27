#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

void EF23non_namespaced_function(void);
int32_t EN3FooV13some_variable = 42;

void EN3FooF13some_function(void)
{
    EF23non_namespaced_function();
}

void EN3BarN6NestedF20some_nested_function(void)
{
    EN3FooF13some_function();
}

void EN3BarN6NestedF23another_nested_function(void)
{
    EN3BarN6NestedF20some_nested_function();
}

int32_t main(void)
{
    int32_t var = EN3FooV13some_variable;
    EN3FooF13some_function();
    EN3BarN6NestedF20some_nested_function();
    EN3BarN6NestedF23another_nested_function();
    return (0);
}
