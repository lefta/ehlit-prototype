#include <stddef.h>
#include <stdint.h>

void* _EF13returning_anyB3any(void* data)
{
    return (data);
}

void** _EF17same_with_ref_anyRB3any(void** data)
{
    void* dummy = _EF13returning_anyB3any(*data);
    return (data);
}

int32_t main(void)
{
    int32_t number = 42;
    number = *(int32_t*)_EF13returning_anyB3any(&number);
    int32_t number2 = *(int32_t*)_EF13returning_anyB3any(&number);
    char* string = "Hello, World!";
    string = (char*)_EF13returning_anyB3any(string);
    char* string2 = (char*)_EF13returning_anyB3any(string);
    int32_t* array;
    array = (int32_t*)_EF13returning_anyB3any(array);
    int32_t* array2 = (int32_t*)_EF13returning_anyB3any(array);
    array[0] = *(int32_t*)_EF13returning_anyB3any(&array[0]);
    int32_t array0 = *(int32_t*)_EF13returning_anyB3any(&array[0]);
    int32_t* rnb = (int32_t*)_EF13returning_anyB3any(&number);
    rnb = (int32_t*)_EF13returning_anyB3any(rnb);
    int32_t** rrnb = (int32_t**)_EF13returning_anyB3any(&rnb);
    *rrnb = (int32_t*)_EF13returning_anyB3any(*rrnb);
    rrnb = (int32_t**)_EF13returning_anyB3any(rrnb);
    rnb = *(int32_t**)_EF17same_with_ref_anyRB3any(&rnb);
    rrnb = (int32_t**)_EF17same_with_ref_anyRB3any(rrnb);
    char** rstring = (char**)_EF17same_with_ref_anyRB3any(&string);
    string = *(char**)_EF17same_with_ref_anyRB3any(rstring);
    void* a1;
    void* a2;
    a1 = a2;
    a1 = _EF13returning_anyB3any(a2);
    return (0);
}
