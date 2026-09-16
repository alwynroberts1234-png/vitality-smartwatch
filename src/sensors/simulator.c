#include "vitality.h"
#include <string.h>
void sensor_simulate(sensor_snapshot_t *s, uint64_t uptime_ms) {
    memset(s, 0, sizeof(*s));
    s->timestamp_ms = uptime_ms;
    s->simulated = true;
    s->valid = VALID_HEART | VALID_SPO2 | VALID_STEPS | VALID_SKIN | VALID_ENVIRONMENT | VALID_BATTERY;
    s->heart_bpm = 72;
    s->spo2_x100 = 9800;
    s->steps = 8421;
    s->skin_c_x100 = 3340;
    s->ambient_c_x100 = 2600;
    s->humidity_x100 = 5200;
    s->pressure_pa = 99900;
    s->altitude_cm = 11800;
    s->battery_mv = 3970;
    s->battery_percent = 78;
}
