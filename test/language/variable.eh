bool global = true
priv int universal_answer = 42
cdecl int cdecl_var = 42
cdecl priv int cdecl_priv_var = 42
priv cdecl int priv_cdecl_var = 42

int main()
{
	static int globint = 42

	int i = 42
	int j

	j = 21
	if i / 2 == j {
		int k
		k = 1
	}

	global = false
	universal_answer = 12
	globint = 12
	cdecl_var = 12
	cdecl_priv_var = 12
	priv_cdecl_var = 12

	return 0
}
