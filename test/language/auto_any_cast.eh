any returning_any(any data)
{
	return data
}

ref any same_with_ref_any(ref any data) {
	any dummy = returning_any(data)
	return data
}

int main()
{
	int number = 42
	number = returning_any(ref number)
	int number2 = returning_any(number)

	str string = "Hello, World!"
  string = returning_any(string)
  str string2 = returning_any(string)

	int[] array
  array = returning_any(array)
  int[] array2 = returning_any(array)
  array[0] = returning_any(array[0])
  int array0 = returning_any(array[0])

	ref int rnb = returning_any(ref number)
	ref rnb = returning_any(rnb)
	ref ref int rrnb = returning_any(ref ref rnb)
	ref rrnb = returning_any(rrnb)
	ref ref rrnb = returning_any(ref ref rrnb)

	ref rnb = same_with_ref_any(rnb)
	ref ref rrnb = same_with_ref_any(rrnb)

	ref str rstring = same_with_ref_any(string)
	string = same_with_ref_any(rstring)

	return 0
}
