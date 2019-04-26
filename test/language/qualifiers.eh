const ref const int print_int(const ref const int i)
{
	return ref i
}

void update_ptrs(restrict ref int32 i, restrict ref int j) {}
void strcpy(restrict str s1, const restrict str s2) {}
void strncpy(restrict str s1, restrict const str s2, size n) {}

volatile int some_register
volatile int some_other_register = cast<ref int>(42)

int main()
{
	const int i = 42
	const ref const int j = ref print_int(ref i)
	ref const int k = ref i
	int l = 21
	const ref int m = ref l
	return 0
}
