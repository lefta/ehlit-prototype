#include <stddef.h>
#include <stdint.h>

void puts(char* s)
{
}

int32_t main(int32_t ac, char** av)
{
    char** av2 = av;
    ac--;
    while (ac)
    {
        ac--;
        av2[ac] = av[ac + 1];
        puts(av[ac]);
    }
    int32_t** sarr1;
    int32_t sarr2[42][5];
    sarr2[12][3] = 42;
    int32_t* arr1[20];
    int32_t(* arr2)[20];
    int32_t(* arr3[12])[20];
    int32_t*(* arr4)[12];
    int32_t(*(* arr5)[12])[20];
    int32_t*(* arr6[20])[12];
    int32_t** arr7[20][12];
    int32_t(** arr8)[12][20];
    int32_t*(* arr9)[20][12];
    int32_t* rarr1[20];
    *rarr1[16] = 42;
    int32_t(* rarr2)[20];
    (*rarr2)[16] = 42;
    int32_t(* rarr3[12])[20];
    (*rarr3[8])[16] = 42;
    int32_t*(* rarr4)[12];
    *(*rarr4)[8] = 42;
    int32_t(*(* rarr5)[12])[20];
    (*(*rarr5)[8])[16] = 42;
    int32_t*(* rarr6[20])[12];
    *(*rarr6[16])[8] = 42;
    int32_t** rarr7[20][12];
    **rarr7[16][8] = 42;
    int32_t(** rarr8)[12][20];
    (**rarr8)[8][16] = 42;
    int32_t*(* rarr9)[20][12];
    *(*rarr9)[16][8] = 42;
    return (0);
}
