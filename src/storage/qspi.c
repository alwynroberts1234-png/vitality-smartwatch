#include "asset_manager.h"
#include <zephyr/storage/flash_map.h>
asset_store_t qspi_assets;
static const struct flash_area *area;
static int read_flash(void *ctx, uint32_t offset, void *dst, size_t size) {
    return flash_area_read((const struct flash_area *)ctx,offset,dst,size);
}
int qspi_assets_init(void) {
    int rc=flash_area_open(FIXED_PARTITION_ID(vitality_assets_partition),&area);
    if(rc) return rc;
    rc=asset_mount(&qspi_assets,read_flash,(void *)area,area->fa_size);
    if(rc) flash_area_close(area);
    return rc;
}
