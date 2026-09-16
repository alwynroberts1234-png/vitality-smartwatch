#pragma once

typedef struct {
    unsigned int bg;
    unsigned int primary;
    unsigned int secondary;
    unsigned int accent;
    unsigned int text;
    unsigned int muted;
} vitality_theme_t;

static const vitality_theme_t THEME_VITALITY_FLOW = {
    .bg = 0x020B14,
    .primary = 0x00C8FF,
    .secondary = 0x21E6A4,
    .accent = 0x4F8CFF,
    .text = 0xF7FBFF,
    .muted = 0x8CA5B8,
};

static const vitality_theme_t THEME_NATURE = {
    .bg = 0x06120C,
    .primary = 0x5DE36C,
    .secondary = 0x25C78A,
    .accent = 0xD7F75C,
    .text = 0xF4FFF4,
    .muted = 0x9BB9A1,
};

static const vitality_theme_t THEME_CLINICAL = {
    .bg = 0xF7FBFF,
    .primary = 0x1B84FF,
    .secondary = 0x00AEBB,
    .accent = 0x7857FF,
    .text = 0x10243A,
    .muted = 0x60758C,
};

static const vitality_theme_t THEME_SPORT = {
    .bg = 0x070707,
    .primary = 0xFF5A36,
    .secondary = 0x00E0FF,
    .accent = 0xA3FF12,
    .text = 0xFFFFFF,
    .muted = 0x9A9A9A,
};

static const vitality_theme_t THEME_MINIMAL = {
    .bg = 0x000000,
    .primary = 0xFFFFFF,
    .secondary = 0xFFFFFF,
    .accent = 0xFFFFFF,
    .text = 0xFFFFFF,
    .muted = 0x8B8B8B,
};

static const vitality_theme_t THEME_RECOVERY = {
    .bg = 0x09071A,
    .primary = 0x8B6CFF,
    .secondary = 0x4FD1FF,
    .accent = 0xEE79FF,
    .text = 0xF7F1FF,
    .muted = 0x988DAF,
};

