#include "asset_manager.h"
#include <string.h>
static uint32_t le32(const uint8_t *p) { return (uint32_t)p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24; }
static uint16_t le16(const uint8_t *p) { return (uint16_t)(p[0] | (uint16_t)p[1]<<8); }
int asset_mount(asset_store_t *s, asset_reader_t read, void *ctx, uint32_t capacity) {
    uint8_t h[ASSET_HEADER_SIZE];
    if (!s) return -1;
    memset(s, 0, sizeof(*s));
    if (!read || capacity < sizeof(h) || read(ctx, 0, h, sizeof(h))) return -1;
    uint32_t count = le32(h+4), total = le32(h+8);
    if (memcmp(h,"VPK1",4) || le32(h+12)!=1 || count>ASSET_MAX_COUNT ||
        total>capacity || total<ASSET_HEADER_SIZE+count*ASSET_ENTRY_SIZE) return -1;
    s->read=read; s->context=ctx; s->capacity=capacity; s->total=total; s->count=count;
    return 0;
}
int asset_find(const asset_store_t *s, const char *name, asset_info_t *out) {
    if (!s || !s->read || !name || !out || strlen(name)>=64) return -1;
    for (uint32_t i=0; i<s->count; ++i) {
        uint8_t e[ASSET_ENTRY_SIZE];
        if (s->read(s->context, ASSET_HEADER_SIZE+i*ASSET_ENTRY_SIZE,e,sizeof(e))) return -1;
        if (!memchr(e,0,64)) return -1;
        if (strcmp((const char *)e,name)) continue;
        out->offset=le32(e+64); out->size=le32(e+68); out->crc=le32(e+72);
        out->width=le16(e+76); out->height=le16(e+78);
        if (out->offset<ASSET_HEADER_SIZE+s->count*ASSET_ENTRY_SIZE ||
            out->offset>s->total || out->size>s->total-out->offset) return -1;
        return 0;
    }
    return -1;
}
int asset_read(const asset_store_t *s, const asset_info_t *a, uint32_t off, void *dst, size_t size) {
    if (!s || !s->read || !a || !dst || a->offset>s->total || a->size>s->total-a->offset || off>a->size || size>a->size-off) return -1;
    return s->read(s->context,a->offset+off,dst,size);
}
int asset_verify(const asset_store_t *s, const asset_info_t *a) {
    uint8_t buffer[256]; uint32_t crc=0xffffffffu;
    if (!s || !a) return -1;
    for (uint32_t off=0; off<a->size;) {
        size_t n=a->size-off; if(n>sizeof(buffer)) n=sizeof(buffer);
        if(asset_read(s,a,off,buffer,n)) return -1;
        for(size_t i=0;i<n;++i) {
            crc ^= buffer[i];
            for(int bit=0;bit<8;++bit) crc=(crc>>1)^((crc&1u)?0xedb88320u:0u);
        }
        off+=(uint32_t)n;
    }
    return (crc^0xffffffffu)==a->crc ? 0 : -1;
}
