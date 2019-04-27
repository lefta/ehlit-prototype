#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

void _EF9take_charB4char(int8_t c)
{
}

int32_t main(void)
{
    int8_t c = 'c';
    _EF9take_charB4char('\a');
    _EF9take_charB4char('\b');
    _EF9take_charB4char('\e');
    _EF9take_charB4char('\f');
    _EF9take_charB4char('\n');
    _EF9take_charB4char('\r');
    _EF9take_charB4char('\t');
    _EF9take_charB4char('\v');
    _EF9take_charB4char('\\');
    int8_t space = ' ';
    return (0);
}
