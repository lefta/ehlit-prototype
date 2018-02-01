#include <stddef.h>
#include <stdint.h>

void* returning_any(void* data)
{
    return (data);
}

int32_t main(void)
{
    int32_t number = 42;
    number = *(int32_t*)returning_any(&number);
    int32_t number2 = *(int32_t*)returning_any(&number);
    char* string = "Hello, World!";
    string = (char*)returning_any(string);
    char* string2 = (char*)returning_any(string);
    return (0);
}
