#include "vitality.h"
void vitality_update(watch_state_t *s) {
    /* Scores are a UI fixture, not inferred from unvalidated PPG algorithms. */
    s->score_valid = s->sensors.simulated;
    if (!s->score_valid) {
        s->vitality = s->movement = s->recovery = s->heart = s->sleep = s->balance = 0;
        return;
    }
    s->movement = 78; s->recovery = 88; s->heart = 81; s->sleep = 84; s->balance = 81;
    s->vitality = (uint8_t)((35u*s->movement + 30u*s->recovery + 20u*s->heart + 15u*s->balance + 50u)/100u);
}
