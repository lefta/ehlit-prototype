int set_int(ref int i)
{
	i = 42
	return i
}

ref int set_int_to(ref int i, ref int j)
{
	i = j
	return ref i
}

ref int set_int_ref(ref int i, ref int j)
{
	ref i = ref j
	return ref i
}

ref ref int set_int_ref_ref(ref ref int i, ref ref int j) {
	ref ref i = ref ref j
	return ref ref i
}

void set_int_ref_lv2(ref ref int i, ref ref int j) {
	ref i = ref j
}

int main()
{
	int i
	ref int j = 21

	i = set_int(ref i)
	ref j = ref set_int_to(ref i, ref j)
	j = set_int_ref(ref i, ref j)

	ref ref int k = ref ref j
	k = 42
	ref k = j
	ref ref k = set_int_ref_ref(ref ref j, ref ref k)

	return 0
}
