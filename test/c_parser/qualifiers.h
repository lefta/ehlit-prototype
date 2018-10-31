int const* const print_int(int const* const i);
void update_ptrs(int* restrict i, int* restrict j);
void strcpy(char* restrict s1, char* const restrict s2);
void strncpy(char* restrict s1, char* const restrict s2, int n);

int volatile some_register;
