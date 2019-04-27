/* Test for testing comments
	 * and / are allowed in multiline comments, but not both of them
*/

/**/
// Defining a stub printf function for testing
/*return*/void/*name*/printf/*start_args*/(/*arg_type*/str/*arg_name*/ s/*end of args*/) /* empty definition */ {}

/* Here starts the program */
int main(int ac, str[] /* char** */ av)
{
  /*
    printf is really cool for printing stuff !
    Okay, ours is quite useless, but still...
  */
	printf(/*start printed*/"Hello, world!\n"/*end printed*/)
	return /* also here ? */0 // 0 means everything got well
}
