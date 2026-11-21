#include <stdio.h>
#include "pico/stdlib.h"
#include "pico/rand.h"
#include "hardware/rosc.h"
#include <string.h>




void configure_rosc() {

    // Then enable the ROSC with MEDIUM range in one write
    rosc_write(&rosc_hw->ctrl, 
        (ROSC_CTRL_ENABLE_VALUE_ENABLE << ROSC_CTRL_ENABLE_LSB) | 
        ROSC_CTRL_FREQ_RANGE_VALUE_MEDIUM);

    rosc_write(&rosc_hw->ctrl, 
        (ROSC_CTRL_ENABLE_VALUE_ENABLE << ROSC_CTRL_ENABLE_LSB) | 
        ROSC_CTRL_FREQ_RANGE_VALUE_HIGH);

    rosc_write(&rosc_hw->freqa,
        (0x9696 << 16) |   // Password
        (0x1 << 7)     |   // DS1_RANDOM = 1 (RP2350 only)
        (0x1 << 3)     |   // DS0_RANDOM = 1 (RP2350 only)
        (0x1 << 0));       // DS0 = double drive

    // FREQB: set stage 4 (DS4) to double drive (0x1)
    rosc_write(&rosc_hw->freqb,
        (0x9696 << 16) |   // Password
        (0x1 << 0));       // DS4 = double drive

    //Wait until ROSC stabilizes
    while (!(rosc_hw->status & ROSC_STATUS_STABLE_BITS)) {
        tight_loop_contents();
    }

}

inline uint8_t rosc_get_byte(void) {
    uint8_t byte = 0;
    for (int bit = 0; bit < 8; bit++) {
        byte = (byte << 1) | (rosc_hw->randombit & 1u);
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
        
    uint8_t randomBytes[125];
    randombytes(randomBytes,125);

    //Initialize UART
    uart_init(uart0, 115200);
    gpio_set_function(0, GPIO_FUNC_UART);
    sleep_ms(5);

    uart_write_blocking(uart0, randomBytes, 125);

    uart_tx_wait_blocking(uart0);
    return 0;
}
