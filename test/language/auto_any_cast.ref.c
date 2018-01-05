
void* returning_any(void* data)
{
    return (data);
}

int main(void)
{
    int number = 42;
    number = *(int*)returning_any(&number);
    int number2 = *(int*)returning_any(&number);
    return (0);
}
