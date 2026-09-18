#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include "driver/gpio.h"
#include "driver/ledc.h"
#include "freertos/FreeRTOS.h"
#include "freertos/projdefs.h"
#include "freertos/task.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_err.h"
#include "hal/adc_types.h"
#include "hal/ledc_types.h"




#define LED GPIO_NUM_2

void app_main(void){

    // make adc1 adc1_handle
    adc_oneshot_unit_handle_t adc1_handle;
    
    // mke adc1 init config
    adc_oneshot_unit_init_cfg_t init_config1 = {
        .unit_id = ADC_UNIT_1,
        .ulp_mode = ADC_ULP_MODE_DISABLE,
    };
    
    // make a new adc1 unit
    ESP_ERROR_CHECK(adc_oneshot_new_unit(&init_config1, &adc1_handle));

    // set resolution to default 
    adc_oneshot_chan_cfg_t config = {
    .bitwidth = ADC_BITWIDTH_DEFAULT,
    .atten = ADC_ATTEN_DB_12,
    };

    // configure channels 6 and 7 because i chose pins 34 and 35
    ESP_ERROR_CHECK(adc_oneshot_config_channel(adc1_handle, ADC_CHANNEL_6, &config));
    ESP_ERROR_CHECK(adc_oneshot_config_channel(adc1_handle, ADC_CHANNEL_7, &config));
    
        
    // configure PWM for motor 1
    ledc_timer_config_t pwm = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .duty_resolution = LEDC_TIMER_8_BIT,
        .timer_num = LEDC_TIMER_0,
        .freq_hz = 20000,
        .clk_cfg = LEDC_AUTO_CLK,
    };
    ESP_ERROR_CHECK(ledc_timer_config(&pwm));

    // configure PWM channel for motor 1
    ledc_channel_config_t pwmChannel0 = {
        .gpio_num = 25,
        .speed_mode= LEDC_LOW_SPEED_MODE,
        .channel = LEDC_CHANNEL_0,
        .intr_type = LEDC_INTR_DISABLE,
        .timer_sel = LEDC_TIMER_0,
        .duty = 0,
        .hpoint = 0
    };
    ESP_ERROR_CHECK(ledc_channel_config(&pwmChannel0));

    ledc_channel_config_t pwmChannel1 = {
        .gpio_num = 26,
        .speed_mode= LEDC_LOW_SPEED_MODE,
        .channel = LEDC_CHANNEL_1,
        .intr_type = LEDC_INTR_DISABLE,
        .timer_sel = LEDC_TIMER_0,
        .duty = 0,
        .hpoint = 0
    };
    ESP_ERROR_CHECK(ledc_channel_config(&pwmChannel1)); 
    

    while (1){

    

        // read adc1 raw analog output
        int adc1_VRx;
        int adc1_VRy;
        adc_oneshot_read(adc1_handle, ADC_CHANNEL_6, &adc1_VRx);
        adc_oneshot_read(adc1_handle, ADC_CHANNEL_7, &adc1_VRy);
        
        // mapping
        int8_t digital_VRx, digital_VRy;
        // VRx mapping
        if (adc1_VRx >= 1950 && adc1_VRx <= 1959) {
            // center
            digital_VRx = 0;
        }
        else if ( adc1_VRx < 1950){
            // negative (left)
            digital_VRx = ( (99 * adc1_VRx) /1949) - 100;
        }
        else{
            // positive (right)
            digital_VRx = 1 + ((adc1_VRx - 1960) * 99) / (4095 - 1960);
        }
        
        // VRy mapping
        if (adc1_VRy >= 1887 && adc1_VRy <= 1894) {
            // center
            digital_VRy = 0;
        }
        else if (adc1_VRy < 1887) {
            // negative side
            digital_VRy = ((99 * adc1_VRy) / 1886) - 100;
        }
        else {
            // positive side
            digital_VRy = 1 + ((adc1_VRy - 1895) * 99) / (4095 - 1895);
        }

        // extra deadzone 
        if (digital_VRx >= -3 && digital_VRx <= 3)
        digital_VRx = 0;
        
        if (digital_VRy >= -3 && digital_VRy <= 3)
        digital_VRy = 0;

        // Control pwm with joystick
        uint32_t duty;
        if ( digital_VRy > 0) {
            // forward
            duty = digital_VRy * 255 / 100;
            ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_1, duty);
            ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, 0);
            ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);
        }
        else if ( digital_VRy < 0){
            // backward
            duty = abs(digital_VRy) * 255 / 100;
            ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_1, 0);
            ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, duty);
            ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);
        }
        else {
            // stop
            ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_1, 0);
            ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, 0);
            ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);
        }


        // print value
        vTaskDelay(pdMS_TO_TICKS(200));
        printf("X: %d ,Y: %d\n", digital_VRx, digital_VRy );

    }

}
