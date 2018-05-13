#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

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
    int32_t(* rarr2)[20];
    int32_t(* rarr3[12])[20];
    int32_t*(* rarr4)[12];
    int32_t(*(* rarr5)[12])[20];
    int32_t*(* rarr6[20])[12];
    int32_t** rarr7[20][12];
    int32_t(** rarr8)[12][20];
    int32_t*(* rarr9)[20][12];
    return (0);
}
