#include "vitality.h"
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(vitality, LOG_LEVEL_INF);
#ifdef CONFIG_VITALITY_SENSOR_SIMULATOR
static void sensor_thread(void *a, void *b, void *c) {
    ARG_UNUSED(a); ARG_UNUSED(b); ARG_UNUSED(c);
    for (;;) {
        app_event_t event = {.type = EV_SENSOR};
        sensor_simulate(&event.sensors, (uint64_t)k_uptime_get());
        if (event_post(&event)) LOG_WRN("Sensor event queue full");
        k_sleep(K_SECONDS(1));
    }
}
K_THREAD_DEFINE(sensor_tid, 1536, sensor_thread, NULL, NULL, NULL, 7, 0, 0);
#endif
int main(void) {
    watch_state_t state;
    watch_init(&state);
    LOG_INF("Vitality prototype: unavailable hardware remains invalid");
#ifdef CONFIG_VITALITY_UI
    if (ui_init()) { LOG_ERR("Display initialization failed"); return 0; }
    ui_render(&state);
#endif
    for (;;) {
        app_event_t event;
        int wait_ms = state.power == POWER_SLEEP ? 1000 : 25;
        if (!event_take(&event, wait_ms)) {
            watch_dispatch(&state, &event);
            if (event.type == EV_SENSOR) {
                LOG_INF("%s HR=%u steps=%u vitality=%u valid=%u",
                    state.sensors.simulated ? "SIMULATED" : "HARDWARE",
                    state.sensors.heart_bpm, state.sensors.steps,
                    state.vitality, state.score_valid);
            }
#ifdef CONFIG_VITALITY_UI
            ui_render(&state);
#endif
        }
#ifdef CONFIG_VITALITY_UI
        if (state.power != POWER_SLEEP) ui_poll();
#endif
    }
}
