void puts(str s) {}

int main(int ac, str[] av)
{
	str[ ] av2 = av
	ac--
	while ac
	{
		ac--
		av2[ac] = av[ac + 1]
		puts(av[ac])
	}

	int[][] sarr1
	int[42][5] sarr2
	sarr2[12][3] = 42

	int[20][] arr1
	int[][20] arr2
	int[12][][20] arr3
	int[][12][] arr4
	int[][12][][20] arr5
	int[20][][12][] arr6
	int[20][12][][] arr7
	int[][][12][20] arr8
	int[][20][12][] arr9

	ref[20] int rarr1
	rarr1[16] = 42
	ref int[20] rarr2
	rarr2[16] = 42
	ref[12] int[20] rarr3
	rarr3[8][16] = 42
	ref ref[12] int rarr4
	rarr4[8] = 42
	ref ref[12] int[20] rarr5
	rarr5[8][16] = 42
	ref[20] ref[12] int rarr6
	rarr6[16][8] = 42
	ref[20][12] ref int rarr7
	rarr7[16][8] = 42
	ref ref int[12][20] rarr8
	rarr8[8][16] = 42
	ref ref[20][12] int rarr9
	rarr9[16][8] = 42

	return 0
}
