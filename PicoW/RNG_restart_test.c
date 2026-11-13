#include <stdio.h>
#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "mlkem_native.h" 
#include "./src/kem.h"
#include "pico/rand.h"
#include "hardware/structs/systick.h"



// ROSC_BASE 0x40060000



// Hardware address of the RP2040/RP2350 ROSC RANDOMBIT register
//#define ROSC_RANDOMBIT_ADDR 0x00

int randombytes(uint8_t *out, size_t outlen) {
    while (outlen >= 4) {
        uint32_t r = get_rand_32();
        memcpy(out, &r, 4);
        out += 4;
        outlen -= 4;
    }
    if (outlen > 0) {
        uint32_t r = get_rand_32();
        memcpy(out, &r, outlen);
    }
    return 0;
}

// void setup_ROSC(uint8_t strengthLevel) {
    
    
//     uint32_t lvl = strengthLevel & 0x7;
//     ROSC_BASE
//     // 1. Ensure ROSC is enabled (Magic enable value 0xfab in bits [23:12])
//     rosc_hw->ctrl = (ROSC_CTRL_ENABLE_VALUE_ENABLE << ROSC_CTRL_ENABLE_LSB);
    
//     // 2. Pack the drive strength into all 4 stages of FREQA and FREQB
//     // Requires magic password 0x9696 in upper 16 bits
//     uint32_t freq_val = (ROSC_FREQA_PASSWD_VALUE_PASS << ROSC_FREQA_PASSWD_LSB) |
//                         (ds << ROSC_FREQA_DS0_LSB) |
//                         (ds << ROSC_FREQA_DS1_LSB) |
//                         (ds << ROSC_FREQA_DS2_LSB) |
//                         (ds << ROSC_FREQA_DS3_LSB);

//     rosc_hw->freqa = freq_val;
//     rosc_hw->freqb = freq_val;

//     // 3. Optional: Set ROSC clock divider to 1 (0xaa0 + 1 = 0xaa1)
//     rosc_hw->div = ROSC_DIV_VALUE_PASS + 1;

//     // 4. Wait until the ROSC reports it is running and stable
//     while (!(rosc_hw->status & ROSC_STATUS_STABLE_BITS)) {
//         tight_loop_contents();
//     }
// }

int main() {

    // systick_hw->csr = 0x5;
    // systick_hw->rvr = 0x00FFFFFF;

    // uint32_t start_cycles = systick_hw->cvr;

    // uint32_t cycles_taken = (start_cycles - systick_hw->cvr) & 0x00FFFFFF;

    // char msg1[64];
    // snprintf(msg1, sizeof(msg1), "Clock Cycles: %lu\r\n", cycles_taken);
    // uart_puts(uart0, msg1);


    
    
    uint gpio_pin = 15;
    uint gpio_pin1 = 28;

    gpio_init(gpio_pin);
    gpio_set_dir(gpio_pin, GPIO_OUT);

    gpio_init(gpio_pin1);
    gpio_set_dir(gpio_pin1, GPIO_OUT);
    
    uint8_t randomBytes[125];
    randombytes(randomBytes,125);

    stdio_init_all();

    if (cyw43_arch_init()) {
        return -1;
    }


    uart_init(uart0, 115200);
    gpio_set_function(0, GPIO_FUNC_UART);
    sleep_ms(10);

    uart_write_blocking(uart0, randomBytes, 125);

    uart_tx_wait_blocking(uart0);
    
    cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 1);
    
    while(true){};
    

    // uint8_t publicKey[MLKEM512_PUBLICKEYBYTES];
    // uint8_t secretKey[MLKEM512_SECRETKEYBYTES];
    // uint8_t cipherText[MLKEM512_CIPHERTEXTBYTES];
    // uint8_t shared_secret_sender[MLKEM512_BYTES];
    // uint8_t shared_secret_recv[MLKEM512_BYTES];

    // for(int i = 0;i < 20;i++){
    //     cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 1);
    //     gpio_put(gpio_pin, true);  // Turn high
    //     if (mlk_kem_keypair(publicKey, secretKey, NULL) == 0) {
    //         printf("Bob - ML-KEM-512 Keypair generated successfully.\n");
    //     }
    //     gpio_put(gpio_pin, false);  // Turn high

    //     gpio_put(gpio_pin1, true);  // Turn high
    //     if (mlk_kem_enc(cipherText, shared_secret_sender, publicKey, NULL) == 0) {
    //         //printf("Alice - ML-KEM-512 Encapsulation complete.\n");
    //     }
    //     if (mlk_kem_dec(shared_secret_recv, cipherText, secretKey, NULL) == 0) {
    //         //printf("Bob - ML-KEM-512 Decapsulation complete.\n");
    //     }
    //     gpio_put(gpio_pin1, false);  // Turn high
        
    //     if (memcmp(shared_secret_recv, shared_secret_sender, MLKEM512_BYTES) == 0) {
    //         printf("Success: Keys match perfectly!\n");
    //     } else {
    //         printf("Error: Key mismatch!\n");
    //     }
    //     cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 0);
    //     sleep_ms(1000);
    // }
    return 0;
}
