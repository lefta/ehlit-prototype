#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

char* EF7strjoinaB3str(char** ary);

int32_t main(void)
{
    int32_t __gen_fun_1[] = { 42, 12, 36 };
    int32_t* ary = __gen_fun_1;
    char* __gen_fun_2[] = { "Hello", "World" };
    char* joined = EF7strjoinaB3str(__gen_fun_2);
    return (0);
}
