#define NO_VALUE
#define CONSTANT 42
#define VALUE (1 << 15)
#define PARENTHESISED_VALUE (42)
#define MACROCEPTION CONSTANT
#define MACROCEPTION_PARENS (CONSTANT)
#define MACROFUNC(a, b) (a+b)
#define MACROFUNC_NO_BODY(a, b)

#define MACRO_TYPE_CHAR char
#define MACRO_TYPE_UCHAR unsigned char
#define MACRO_TYPE_SCHAR signed char
#define MACRO_TYPE_SHORT short
#define MACRO_TYPE_INT int
#define MACRO_TYPE_LONG long
#define MACRO_TYPE_LLONG long long
#define MACRO_TYPE_FLOAT float
#define MACRO_TYPE_DOUBLE double
#define MACRO_TYPE_LDOUBLE long double
#define MACRO_TYPE_STR char*
