#include "vitality.h"
#include "asset_manager.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do { if(!(x)) {fprintf(stderr,"FAIL %s:%d: %s\n",__FILE__,__LINE__,#x); exit(1);} } while(0)
typedef struct {const unsigned char *bytes;size_t size;} memory_t;
static int read_memory(void *ctx,uint32_t offset,void *dst,size_t n) {
    memory_t *m=ctx;if(offset>m->size||n>m->size-offset)return -1;
    memcpy(dst,m->bytes+offset,n);return 0;
}
static void put32(unsigned char *p,uint32_t value) {for(int i=0;i<4;i++)p[i]=(unsigned char)(value>>(8*i));}
static void test_assets(void) {
    unsigned char pack[105]={0},data[10]={0};asset_store_t store;asset_info_t info;
    memory_t memory={pack,sizeof(pack)};
    memcpy(pack,"VPK1",4);put32(pack+4,1);put32(pack+8,sizeof(pack));put32(pack+12,1);
    memcpy(pack+16,"icons/test.bin",15);put32(pack+80,96);put32(pack+84,9);put32(pack+88,0xcbf43926);
    memcpy(pack+96,"123456789",9);
    CHECK(!asset_mount(&store,read_memory,&memory,sizeof(pack)));
    CHECK(!asset_find(&store,"icons/test.bin",&info));
    CHECK(!asset_verify(&store,&info));
    CHECK(!asset_read(&store,&info,3,data,3));CHECK(!memcmp(data,"456",3));
    CHECK(asset_read(&store,&info,8,data,2)!=0);
    CHECK(asset_read(&store,&info,UINT32_MAX,data,1)!=0);
    CHECK(asset_find(&store,"missing",&info)!=0);
    pack[104]^=1;CHECK(asset_verify(&store,&info)!=0);pack[104]^=1;
    put32(pack+80,UINT32_MAX);CHECK(asset_find(&store,"icons/test.bin",&info)!=0);put32(pack+80,96);
    put32(pack+84,UINT32_MAX);CHECK(asset_find(&store,"icons/test.bin",&info)!=0);put32(pack+84,9);
    CHECK(asset_mount(&store,read_memory,&memory,104)!=0);
    CHECK(asset_find(&store,"icons/test.bin",&info)!=0);
    pack[0]=0;CHECK(asset_mount(&store,read_memory,&memory,sizeof(pack))!=0);pack[0]='V';
    put32(pack+4,129);CHECK(asset_mount(&store,read_memory,&memory,sizeof(pack))!=0);
}
static void test_state(void) {
    watch_state_t state;watch_init(&state);
    CHECK(!state.sensors.valid&&!state.score_valid&&!state.sensors.simulated);
    app_event_t e={0};e.type=EV_PREVIOUS;watch_dispatch(&state,&e);CHECK(state.screen==SCREEN_SETTINGS);
    e.type=EV_NEXT;watch_dispatch(&state,&e);CHECK(state.screen==SCREEN_HOME);
    e.type=EV_THEME_NEXT;for(int i=0;i<6;i++)watch_dispatch(&state,&e);CHECK(state.theme==0);
    e.type=EV_SLEEP;watch_dispatch(&state,&e);CHECK(state.power==POWER_SLEEP);
    e.type=EV_WAKE;watch_dispatch(&state,&e);CHECK(state.power==POWER_ACTIVE);
    e.type=EV_WORKOUT_TOGGLE;watch_dispatch(&state,&e);CHECK(state.workout_active&&state.power==POWER_WORKOUT);
    e.type=EV_SLEEP;watch_dispatch(&state,&e);CHECK(state.power==POWER_WORKOUT);
    e.type=EV_WORKOUT_TOGGLE;watch_dispatch(&state,&e);CHECK(!state.workout_active&&state.power==POWER_ACTIVE);
    e.type=EV_SENSOR;sensor_simulate(&e.sensors,1000);watch_dispatch(&state,&e);
    CHECK(state.vitality==82&&state.score_valid&&state.sensors.simulated&&state.sensors.heart_bpm==72);
    e.sensors.timestamp_ms=500;e.sensors.heart_bpm=250;watch_dispatch(&state,&e);CHECK(state.sensors.heart_bpm==72);
    e.sensors.timestamp_ms=2000;e.sensors.simulated=false;watch_dispatch(&state,&e);
    CHECK(!state.score_valid&&state.vitality==0);
}
static void test_generated_pack(const char *filename) {
    FILE *file=fopen(filename,"rb");CHECK(file!=NULL);CHECK(fseek(file,0,SEEK_END)==0);
    long length=ftell(file);CHECK(length>16&&length<0x1400000);rewind(file);
    unsigned char *bytes=malloc((size_t)length);CHECK(bytes!=NULL);CHECK(fread(bytes,1,(size_t)length,file)==(size_t)length);fclose(file);
    memory_t m={bytes,(size_t)length};asset_store_t s;asset_info_t info;
    CHECK(!asset_mount(&s,read_memory,&m,(uint32_t)length));
    CHECK(!asset_find(&s,"logo/mark.bin",&info));CHECK(info.width==48&&info.height==48);CHECK(!asset_verify(&s,&info));
    CHECK(!asset_find(&s,"icons/heart.bin",&info));CHECK(info.width==64&&info.height==64);CHECK(!asset_verify(&s,&info));
    CHECK(!asset_find(&s,"themes/nature.json",&info));CHECK(!asset_verify(&s,&info));free(bytes);
}
int main(int argc,char **argv) {
    test_assets();test_state();if(argc>1)test_generated_pack(argv[1]);
    puts("PASS: core navigation, power transitions, invalid/stale data, demo scoring, asset integrity and bounds.");
    return 0;
}
