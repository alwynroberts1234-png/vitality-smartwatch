#ifndef VITALITY_H
#define VITALITY_H
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#define VITALITY_WIDTH 466
#define VITALITY_HEIGHT 466
#define VITALITY_EVENT_CAPACITY 16
typedef enum { SCREEN_HOME, SCREEN_VITALITY, SCREEN_HEART, SCREEN_ACTIVITY,
    SCREEN_ENVIRONMENT, SCREEN_SETTINGS, SCREEN_COUNT } screen_t;
typedef enum { POWER_ACTIVE, POWER_IDLE, POWER_SLEEP, POWER_WORKOUT } power_state_t;
typedef enum { EV_NEXT, EV_PREVIOUS, EV_HOME, EV_WAKE, EV_IDLE, EV_SLEEP,
    EV_WORKOUT_TOGGLE, EV_THEME_NEXT, EV_SENSOR } event_type_t;
enum { VALID_HEART=1u, VALID_SPO2=2u, VALID_STEPS=4u, VALID_SKIN=8u,
    VALID_ENVIRONMENT=16u, VALID_BATTERY=32u };
typedef struct {
    uint64_t timestamp_ms;
    uint32_t valid;
    bool simulated;
    uint16_t heart_bpm, spo2_x100;
    uint32_t steps;
    int16_t skin_c_x100, ambient_c_x100;
    uint16_t humidity_x100;
    uint32_t pressure_pa;
    int32_t altitude_cm;
    int32_t accel_mg[3], gyro_mdps[3], magnetic_nt[3];
    uint16_t heading_x100, battery_mv;
    uint8_t battery_percent;
} sensor_snapshot_t;
typedef struct { event_type_t type; sensor_snapshot_t sensors; } app_event_t;
typedef struct {
    screen_t screen;
    power_state_t power;
    uint8_t theme;
    bool workout_active;
    bool score_valid;
    uint8_t vitality, movement, recovery, heart, sleep, balance;
    sensor_snapshot_t sensors;
} watch_state_t;
typedef struct {
    int (*init)(void);
    int (*start)(void);
    int (*stop)(void);
    int (*read)(sensor_snapshot_t *sample);
    int (*set_rate)(uint32_t hz);
    int (*suspend)(void);
    int (*resume)(void);
} sensor_driver_api_t;
void watch_init(watch_state_t *state);
void watch_dispatch(watch_state_t *state, const app_event_t *event);
void vitality_update(watch_state_t *state);
void sensor_simulate(sensor_snapshot_t *sample, uint64_t uptime_ms);
int event_post(const app_event_t *event);
int event_take(app_event_t *event, int32_t timeout_ms);
int ui_init(void);
void ui_render(const watch_state_t *state);
void ui_poll(void);
#endif
