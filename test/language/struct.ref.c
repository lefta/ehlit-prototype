#include <stddef.h>
#include <stdint.h>

struct test_struct
{
    int32_t field1;
    char* field2;
    int32_t** field3;
};

int32_t main(void)
{
    struct test_struct t;
    struct test_struct* rt = &t;
    return (0);
}
