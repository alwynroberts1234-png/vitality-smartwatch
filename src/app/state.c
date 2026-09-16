#include "vitality.h"
#include <string.h>
void watch_init(watch_state_t *s) {
    memset(s, 0, sizeof(*s));
    s->power = POWER_ACTIVE;
}
void watch_dispatch(watch_state_t *s, const app_event_t *e) {
    switch(e->type) {
    case EV_NEXT: s->screen = (screen_t)((s->screen + 1) % SCREEN_COUNT); break;
    case EV_PREVIOUS: s->screen = (screen_t)((s->screen + SCREEN_COUNT - 1) % SCREEN_COUNT); break;
    case EV_HOME: s->screen = SCREEN_HOME; break;
    case EV_THEME_NEXT: s->theme = (uint8_t)((s->theme + 1) % 6); break;
    case EV_WAKE: s->power = s->workout_active ? POWER_WORKOUT : POWER_ACTIVE; break;
    case EV_IDLE: if (!s->workout_active) s->power = POWER_IDLE; break;
    case EV_SLEEP: if (!s->workout_active) s->power = POWER_SLEEP; break;
    case EV_WORKOUT_TOGGLE:
        s->workout_active = !s->workout_active;
        s->power = s->workout_active ? POWER_WORKOUT : POWER_ACTIVE;
        break;
    case EV_SENSOR:
        if (e->sensors.timestamp_ms < s->sensors.timestamp_ms) break;
        s->sensors = e->sensors;
        vitality_update(s);
        break;
    default: break;
    }
}
