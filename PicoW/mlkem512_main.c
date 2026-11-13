#include <stdint.h>
#include <stdio.h>
#include "../mlkem/mlkem_native.h" 
#include "../mlkem/src/kem.h"
#include "pico/rand.h"
#include "pico/cyw43_arch.h"
#include "pico/stdlib.h"


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

int main(){

    //Setup GPIO PINS
    uint gpio_pin = 15;
    uint gpio_pin1 = 28;

    gpio_init(gpio_pin);
    gpio_set_dir(gpio_pin, GPIO_OUT);

    gpio_init(gpio_pin1);
    gpio_set_dir(gpio_pin1, GPIO_OUT);

    stdio_init_all();
    
    if (cyw43_arch_init()) {
        return -1;
    }

    cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 1);
    printf("ML-KEM-1024 starting..\r\n");
    sleep_ms(2000);
    cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 0);
    printf("ML-KEM-1024 starting..\r\n");
    sleep_ms(2000);
    cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 1);
    printf("ML-KEM-1024 starting..\r\n");
    sleep_ms(2000);
    cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 0);
    
    uint8_t publicKey[MLKEM512_PUBLICKEYBYTES];
    uint8_t secretKey[MLKEM512_SECRETKEYBYTES];
    uint8_t cipherText[MLKEM512_CIPHERTEXTBYTES];
    uint8_t shared_secret_sender[MLKEM512_BYTES];
    uint8_t shared_secret_recv[MLKEM512_BYTES];

    for(int i = 0;i < 20;i++){
        cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 1);
        gpio_put(gpio_pin, true);  // Turn high
        if (mlk_kem_keypair(publicKey, secretKey, NULL) == 0) {
            printf("Bob - ML-KEM-512 Keypair generated successfully.\n");
        }
        gpio_put(gpio_pin, false);  // Turn high

        gpio_put(gpio_pin1, true);  // Turn high
        if (mlk_kem_enc(cipherText, shared_secret_sender, publicKey, NULL) == 0) {
            //printf("Alice - ML-KEM-512 Encapsulation complete.\n");
        }
        if (mlk_kem_dec(shared_secret_recv, cipherText, secretKey, NULL) == 0) {
            //printf("Bob - ML-KEM-512 Decapsulation complete.\n");
        }
        gpio_put(gpio_pin1, false);  // Turn high
        
        if (memcmp(shared_secret_recv, shared_secret_sender, MLKEM512_BYTES) == 0) {
            printf("Success: Keys match perfectly!\n");
        } else {
            printf("Error: Key mismatch!\n");
        }
        cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 0);
        sleep_ms(1000);
    }
    return 1;
}

