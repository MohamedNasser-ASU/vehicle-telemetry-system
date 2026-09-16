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
    
    // make a new adc1 uniut
    ESP_ERROR_CHECK(adc_oneshot_new_unit(&init_config1, &adc1_handle));

    // set resolution to default 
    adc_oneshot_chan_cfg_t config = {
    .bitwidth = ADC_BITWIDTH_DEFAULT,
    .atten = ADC_ATTEN_DB_12,
    };

    // configure channel 6 because i chose pin 34
    ESP_ERROR_CHECK(adc_oneshot_config_channel(adc1_handle, ADC_CHANNEL_6, &config));
    

    while (1){

        // read adc1 raw analog output
        int adc1_out;
        adc_oneshot_read(adc1_handle, ADC_CHANNEL_6, &adc1_out);
        vTaskDelay(pdMS_TO_TICKS(200));
        printf("%d\n", adc1_out);
    }




    




}
