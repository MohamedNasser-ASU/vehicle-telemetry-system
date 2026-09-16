#include <stdint.h>
#include "driver/gpio.h"
#include "freertos/FreeRTOS.h"
#include "freertos/projdefs.h"
#include "freertos/task.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_err.h"
#include "hal/adc_types.h"


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

    // configure channels 6 and 7 because i chose pins 34 and 45
    ESP_ERROR_CHECK(adc_oneshot_config_channel(adc1_handle, ADC_CHANNEL_6, &config));
    ESP_ERROR_CHECK(adc_oneshot_config_channel(adc1_handle, ADC_CHANNEL_7, &config));
    

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

        // print value
        vTaskDelay(pdMS_TO_TICKS(200));
        printf("X: %d ,Y: %d\n", digital_VRx, digital_VRy );

    }




    




}
