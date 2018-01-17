
int fun(int i, int* j)
{
    return (*j);
}

int* ref_fun(int* i)
{
    return (i);
}

int main(void)
{
    int i;
    int* j;
    j = &i;
    *j = i;
    *j = fun(i, j);
    *j = fun(*j, &i);
    fun(i, j);
    i = *ref_fun(&i);
    *j = *ref_fun(j);
    j = ref_fun(j);
    return (*j);
}
