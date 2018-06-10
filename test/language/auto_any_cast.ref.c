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
    int32_t* array;
    array = (int32_t*)returning_any(array);
    int32_t* array2 = (int32_t*)returning_any(array);
    array[0] = *(int32_t*)returning_any(&array[0]);
    int32_t array0 = *(int32_t*)returning_any(&array[0]);
    int32_t* rnb = (int32_t*)returning_any(&number);
    rnb = (int32_t*)returning_any(rnb);
    int32_t** rrnb = (int32_t**)returning_any(&rnb);
    rrnb = (int32_t**)returning_any(rrnb);
    return (0);
}
