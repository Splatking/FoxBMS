#include "flashing_light.h"
#include "diag.h"
#include "led.h"

static uint8_t ledState = 0u;

void MYM_Init(void) {
    /* Initialize LED if required (optional, depends on LED driver implementation) */
    LED_Set(LED_GENERAL, LED_OFF);
}

void MYM_Trigger(void) {
    /* Example diagnostic trigger */
    DIAG_Handler(DIAG_ID_USER_DEFINED_0, DIAG_EVENT_OK, 0u);

    /* Toggle LED on each call */
    ledState ^= 1u; /* Toggle between 0 and 1 */
    if (ledState == 1u) {
        LED_Set(LED_GENERAL, LED_ON);
    } else {
        LED_Set(LED_GENERAL, LED_OFF);
    }
}