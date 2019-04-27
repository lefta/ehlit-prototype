#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

void EF9take_charB4char(int8_t c)
{
}

int32_t main(void)
{
    int8_t c = 'c';
    EF9take_charB4char('\a');
    EF9take_charB4char('\b');
    EF9take_charB4char('\e');
    EF9take_charB4char('\f');
    EF9take_charB4char('\n');
    EF9take_charB4char('\r');
    EF9take_charB4char('\t');
    EF9take_charB4char('\v');
    EF9take_charB4char('\\');
    int8_t space = ' ';
    return (0);
}
