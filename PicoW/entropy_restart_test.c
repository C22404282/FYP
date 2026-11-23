#include <stdio.h>
#include "pico/stdlib.h"
#include "pico/rand.h"
#include "hardware/rosc.h"
#include <string.h>


#ifndef ROSC_WAIT_CYCLES
#define ROSC_WAIT_CYCLES 25
#endif

void configure_rosc() {

    //Set to medium range first - Uses 6 of 8 stages
    rosc_write(&rosc_hw->ctrl, 
        (ROSC_CTRL_ENABLE_VALUE_ENABLE << ROSC_CTRL_ENABLE_LSB) | 
        ROSC_CTRL_FREQ_RANGE_VALUE_MEDIUM);

    //Set to high range next - Uses stages 4 to 7
    rosc_write(&rosc_hw->ctrl, 
    ROSC_CTRL_FREQ_RANGE_VALUE_HIGH);
    
    rosc_write(&rosc_hw->freqb,
    (0x9696 << 16) |   // Password
    (0x7 << 0) |  //Set stage 4 to quadruple strength
    (0x7 << 4) |  //Set stage 5 to quadruple strength
    (0x7 << 8) |  //Set stage 6 to quadruple strength
    (0x7 << 12)   //Set stage 7 to quadruple strength
    );  

    //Wait until ROSC stabilizes
    while (!(rosc_hw->status & ROSC_STATUS_STABLE_BITS)) {
        tight_loop_contents(); //NOP
    }
}

inline uint8_t rosc_get_byte(void) {
    uint8_t byte = 0;
    for (int bit = 0; bit < 8; bit++) {
        byte = (byte << 1) | (rosc_hw->randombit & 1u);
        rosc_hw->count = ROSC_WAIT_CYCLES; //Wait for 16 cycles to allow for jitter
        while (rosc_hw->count != 0) {
            tight_loop_contents();//NOP
        }
    }
    return byte;
}

int randombytes(uint8_t *out, size_t outlen) {
    for (size_t i = 0; i < outlen; i++) {
        out[i] = rosc_get_byte();
    }
    return 0;
}


int main() {
    configure_rosc();

    uint8_t randomBytes[125];
    randombytes(randomBytes,125);

    //Initialize UART
    uart_init(uart0, 115200);
    gpio_set_function(0, GPIO_FUNC_UART);
    //sleep_ms(5);

    uart_write_blocking(uart0, randomBytes, 125);
    uart_tx_wait_blocking(uart0);
    return 0;
}
