#include "vitality.h"
#include <zephyr/kernel.h>
K_MSGQ_DEFINE(watch_events, sizeof(app_event_t), VITALITY_EVENT_CAPACITY, 4);
int event_post(const app_event_t *event) {
    /* Callers must observe overflow; never silently overwrite user actions. */
    return k_msgq_put(&watch_events, event, K_NO_WAIT);
}
int event_take(app_event_t *event, int32_t timeout_ms) {
    return k_msgq_get(&watch_events, event, K_MSEC(timeout_ms));
}
