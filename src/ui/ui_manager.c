#include "vitality.h"
#include "asset_manager.h"
#include <lvgl.h>
#include <zephyr/device.h>
#include <zephyr/drivers/display.h>
#include <zephyr/logging/log.h>
#include <stdio.h>
LOG_MODULE_REGISTER(watch_ui, LOG_LEVEL_INF);
static lv_obj_t *root, *title, *value, *detail, *badge, *arc;
static const struct device *display;
static const char *names[]={"Vitality Flow","Nature","Clinical","Sport","Minimal","Recovery"};
static const uint32_t bg[]={0x020b14,0x06120c,0xf7fbff,0x070707,0x000000,0x09071a};
static const uint32_t fg[]={0xf7fbff,0xf4fff4,0x10243a,0xffffff,0xffffff,0xf7f1ff};
static const uint32_t primary[]={0x00c8ff,0x5de36c,0x1b84ff,0xff5a36,0xffffff,0x8b6cff};
static void click(lv_event_t *e) {
    app_event_t event={0};
    event.type=(event_type_t)(uintptr_t)lv_event_get_user_data(e);
    if(event_post(&event)) LOG_WRN("UI event queue full");
}
static lv_obj_t *label(int y,const lv_font_t *font) {
    lv_obj_t *obj=lv_label_create(root);
    lv_obj_set_style_text_font(obj,font,0);
    lv_obj_set_width(obj,350);
    lv_obj_set_style_text_align(obj,LV_TEXT_ALIGN_CENTER,0);
    lv_obj_align(obj,LV_ALIGN_TOP_MID,0,y);
    return obj;
}
static void button(const char *text,int x,event_type_t event) {
    lv_obj_t *b=lv_button_create(root);
    lv_obj_set_size(b,88,40);
    lv_obj_align(b,LV_ALIGN_BOTTOM_MID,x,-72);
    lv_obj_set_style_bg_color(b,lv_color_hex(0x15313d),0);
    lv_obj_add_event_cb(b,click,LV_EVENT_CLICKED,(void *)(uintptr_t)event);
    lv_obj_t *l=lv_label_create(b); lv_label_set_text(l,text); lv_obj_center(l);
}
int ui_init(void) {
    display=DEVICE_DT_GET(DT_CHOSEN(zephyr_display));
    if(!device_is_ready(display)) return -1;
    /* Zephyr initializes LVGL and its partial buffers before main. */
    root=lv_screen_active();
    lv_obj_remove_flag(root,LV_OBJ_FLAG_SCROLLABLE);
    arc=lv_arc_create(root); lv_obj_set_size(arc,416,416); lv_obj_center(arc);
    lv_arc_set_rotation(arc,135); lv_arc_set_bg_angles(arc,0,270);
    lv_obj_remove_style(arc,NULL,LV_PART_KNOB);
    lv_obj_remove_flag(arc,LV_OBJ_FLAG_CLICKABLE);
    lv_obj_set_style_arc_width(arc,8,LV_PART_MAIN);
    lv_obj_set_style_arc_width(arc,8,LV_PART_INDICATOR);
    lv_obj_set_style_arc_color(arc,lv_color_hex(0x18303b),LV_PART_MAIN);
    badge=label(78,&lv_font_montserrat_14);
    title=label(120,&lv_font_montserrat_24);
    value=label(163,&lv_font_montserrat_48);
    detail=label(229,&lv_font_montserrat_24);
    button("<",-96,EV_PREVIOUS); button("Home",0,EV_HOME); button(">",96,EV_NEXT);
    lv_obj_t *theme=lv_button_create(root);
    lv_obj_set_size(theme,160,30); lv_obj_align(theme,LV_ALIGN_BOTTOM_MID,0,-33);
    lv_obj_add_event_cb(theme,click,LV_EVENT_CLICKED,(void *)(uintptr_t)EV_THEME_NEXT);
    lv_obj_t *t=lv_label_create(theme); lv_label_set_text(t,"Change theme"); lv_obj_center(t);
#ifdef CONFIG_VITALITY_QSPI_ASSETS
    if(qspi_assets_init()==0) {
        lvgl_qspi_register();
        asset_info_t mark;
        if(asset_find(&qspi_assets,"logo/mark.bin",&mark)==0) {
            lv_obj_t *img=lv_image_create(root);
            lv_image_set_src(img,"Q:/logo/mark.bin");
            lv_obj_align(img,LV_ALIGN_TOP_MID,0,20);
        }
    } else LOG_WRN("No valid QSPI pack; using primitive UI");
#endif
    display_blanking_off(display);
    return 0;
}
void ui_render(const watch_state_t *s) {
    if(s->power==POWER_SLEEP) { display_blanking_on(display); return; }
    display_blanking_off(display);
    uint8_t theme=s->theme%6;
    lv_obj_set_style_bg_color(root,lv_color_hex(bg[theme]),0);
    lv_obj_set_style_text_color(root,lv_color_hex(fg[theme]),0);
    lv_obj_set_style_arc_color(arc,lv_color_hex(primary[theme]),LV_PART_INDICATOR);
    lv_arc_set_value(arc,s->score_valid?s->vitality:0);
    lv_label_set_text(badge,s->sensors.simulated?"SIMULATED DATA":"SENSORS UNAVAILABLE");
    char big[64],small[160];
    const sensor_snapshot_t *d=&s->sensors;
    big[0]=small[0]=0;
    switch(s->screen) {
    case SCREEN_HOME:
        lv_label_set_text(title,"VITALITY");
        snprintf(big,sizeof(big),"%s",s->sensors.simulated?"10:08":"--:--");
        snprintf(small,sizeof(small),"%s\n%lu steps\n%u%% battery",names[theme],(unsigned long)d->steps,d->battery_percent);
        if(!d->valid) snprintf(small,sizeof(small),"%s\nWaiting for sensors",names[theme]);
        break;
    case SCREEN_VITALITY:
        lv_label_set_text(title,"DAILY VITALITY");
        if(s->score_valid) {
            snprintf(big,sizeof(big),"%u",s->vitality);
            snprintf(small,sizeof(small),"Movement %u   Recovery %u\nHeart %u   Sleep %u",s->movement,s->recovery,s->heart,s->sleep);
        } else { snprintf(big,sizeof(big),"--"); snprintf(small,sizeof(small),"No validated score available"); }
        break;
    case SCREEN_HEART:
        lv_label_set_text(title,"HEART RATE");
        if(d->valid&VALID_HEART) snprintf(big,sizeof(big),"%u BPM",d->heart_bpm);
        else snprintf(big,sizeof(big),"-- BPM");
        if(d->valid&VALID_SPO2) snprintf(small,sizeof(small),"SpO2 %u%%\n%s",d->spo2_x100/100,d->simulated?"Demo reading":"Measurement");
        else snprintf(small,sizeof(small),"SpO2 unavailable");
        break;
    case SCREEN_ACTIVITY:
        lv_label_set_text(title,"ACTIVITY");
        if(d->valid&VALID_STEPS) snprintf(big,sizeof(big),"%lu",(unsigned long)d->steps);
        else snprintf(big,sizeof(big),"--");
        snprintf(small,sizeof(small),"STEPS\n%s",s->workout_active?"Workout active":"Daily goal 10,000");
        break;
    case SCREEN_ENVIRONMENT:
        lv_label_set_text(title,"ENVIRONMENT");
        if(d->valid&VALID_ENVIRONMENT) {
            snprintf(big,sizeof(big),"%d C",d->ambient_c_x100/100);
            snprintf(small,sizeof(small),"Humidity %u%%\nAltitude %ld m",d->humidity_x100/100,(long)d->altitude_cm/100);
        } else { snprintf(big,sizeof(big),"-- C"); snprintf(small,sizeof(small),"Environment unavailable"); }
        break;
    default:
        lv_label_set_text(title,"SETTINGS");
        snprintf(big,sizeof(big),"%s",names[theme]);
        snprintf(small,sizeof(small),"Theme button below\n466 x 466 / RGB565");
        break;
    }
    lv_label_set_text(value,big); lv_label_set_text(detail,small);
}
void ui_poll(void) { lv_timer_handler(); }
