#include <stddef.h>

void* returning_any(void* data)
{
    return (data);
}

int main(void)
{
    int number = 42;
    number = *(int*)returning_any(&number);
    int number2 = *(int*)returning_any(&number);
    char* string = "Hello, World!";
    string = (char*)returning_any(string);
    char* string2 = (char*)returning_any(string);
    return (0);
}
