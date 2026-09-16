#include "asset_manager.h"
#include <lvgl.h>
#include <string.h>
typedef struct { bool used; uint32_t position; asset_info_t info; } file_t;
static file_t files[4];
static void *open_cb(lv_fs_drv_t *drv,const char *path,lv_fs_mode_t mode) {
    (void)drv;
    if(mode!=LV_FS_MODE_RD) return NULL;
    while(*path=='/') ++path;
    for(size_t i=0;i<4;++i) if(!files[i].used) {
        if(asset_find(&qspi_assets,path,&files[i].info) || asset_verify(&qspi_assets,&files[i].info)) return NULL;
        files[i].used=true; files[i].position=0; return &files[i];
    }
    return NULL;
}
static lv_fs_res_t close_cb(lv_fs_drv_t *drv,void *file) {
    (void)drv; ((file_t *)file)->used=false; return LV_FS_RES_OK;
}
static lv_fs_res_t read_cb(lv_fs_drv_t *drv,void *file,void *dst,uint32_t size,uint32_t *read_size) {
    (void)drv; file_t *f=file; *read_size=0;
    uint32_t n=f->info.size-f->position; if(n>size)n=size;
    if(asset_read(&qspi_assets,&f->info,f->position,dst,n))return LV_FS_RES_FS_ERR;
    f->position+=n; *read_size=n; return LV_FS_RES_OK;
}
static lv_fs_res_t seek_cb(lv_fs_drv_t *drv,void *file,uint32_t pos,lv_fs_whence_t whence) {
    (void)drv; file_t *f=file;
    uint32_t base=whence==LV_FS_SEEK_SET?0:whence==LV_FS_SEEK_CUR?f->position:f->info.size;
    if(whence!=LV_FS_SEEK_SET && whence!=LV_FS_SEEK_CUR && whence!=LV_FS_SEEK_END)return LV_FS_RES_INV_PARAM;
    if(pos>f->info.size-base)return LV_FS_RES_INV_PARAM;
    f->position=base+pos; return LV_FS_RES_OK;
}
static lv_fs_res_t tell_cb(lv_fs_drv_t *drv,void *file,uint32_t *pos) {
    (void)drv; *pos=((file_t *)file)->position; return LV_FS_RES_OK;
}
void lvgl_qspi_register(void) {
    static lv_fs_drv_t driver;
    lv_fs_drv_init(&driver); driver.letter='Q';
    driver.open_cb=open_cb; driver.close_cb=close_cb; driver.read_cb=read_cb;
    driver.seek_cb=seek_cb; driver.tell_cb=tell_cb; lv_fs_drv_register(&driver);
}
