#ifndef ASSET_MANAGER_H
#define ASSET_MANAGER_H
#include <stdint.h>
#include <stddef.h>
#define ASSET_ENTRY_SIZE 80u
#define ASSET_HEADER_SIZE 16u
#define ASSET_MAX_COUNT 128u
/* VPK1 little-endian: header magic,count,total size,version.
 * Each entry: UTF-8 name[64], offset u32, size u32, CRC32 u32,
 * width u16,height u16. Payload is opaque: .bin is LVGL v9 RGB565. */
typedef int (*asset_reader_t)(void *context, uint32_t offset, void *dst, size_t size);
typedef struct { asset_reader_t read; void *context; uint32_t capacity, total, count; } asset_store_t;
typedef struct { uint32_t offset, size, crc; uint16_t width, height; } asset_info_t;
int asset_mount(asset_store_t *store, asset_reader_t read, void *context, uint32_t capacity);
int asset_find(const asset_store_t *store, const char *name, asset_info_t *info);
int asset_read(const asset_store_t *store, const asset_info_t *info, uint32_t offset, void *dst, size_t size);
int asset_verify(const asset_store_t *store, const asset_info_t *info);
int qspi_assets_init(void);
extern asset_store_t qspi_assets;
void lvgl_qspi_register(void);
#endif
