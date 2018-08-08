#include <stddef.h>
#include <stdint.h>

void* function(void)
{
    return (NULL);
}

void get_null(void* p)
{
}

int32_t main(void)
{
    char* s = NULL;
    get_null(NULL);
    return (0);
}
