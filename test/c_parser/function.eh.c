#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <c_parser/function.h>

int32_t main(void)
{
    int32_t i;
    vargs_fun_no_arg();
    vargs_fun_no_arg(NULL);
    vargs_fun_no_arg(i, NULL);
    vargs_fun_args(i);
    vargs_fun_args(i, i, &i);
}
