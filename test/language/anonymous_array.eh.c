#include <stddef.h>
#include <stdint.h>

char* _EF7strjoinAB3str(char** ary);

int32_t main(void)
{
    int32_t __gen_fun_1[] = { 42, 12, 36 };
    int32_t* ary = __gen_fun_1;
    char* __gen_fun_2[] = { "Hello", "World" };
    char* joined = _EF7strjoinAB3str(__gen_fun_2);
    return (0);
}
