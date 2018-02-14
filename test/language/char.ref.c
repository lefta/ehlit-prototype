#include <stddef.h>
#include <stdint.h>

void take_char(int8_t c)
{
}

int32_t main(void)
{
    int8_t c = 'c';
    take_char('\a');
    take_char('\b');
    take_char('\e');
    take_char('\f');
    take_char('\n');
    take_char('\r');
    take_char('\t');
    take_char('\v');
    take_char('\\');
    return (0);
}
