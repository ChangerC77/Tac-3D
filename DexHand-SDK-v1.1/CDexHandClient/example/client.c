// client.c
// DexHand client example
//
// copyright (C) 2024 - 2024 by pingplug
//
#include "dexhand_client.h"

#include <math.h>
#include <stdio.h>

#ifdef _WIN32
#include <windows.h>

void
sleep_sec(double time)
{
    uint32_t msec = round(time * 1e3);
    Sleep(msec);
}
#else
#include <unistd.h>

void
sleep_sec(double time)
{
    uint32_t usec = round(time * 1e6);
    usleep(usec);
}
#endif

// callback functions
void hand_cb(const dexhand_ctx *ctx);
void term_cb();

int
main()
{
    // set log level
    dh_set_log("log.txt", DH_LL_DBG);
    // init context
    dexhand_ctx *ctx;
    if (dh_dexhand_client(&ctx, "192.168.2.100", 60031, term_cb, hand_cb) < 0) {
        printf("Can not init context, exit\n");
        return -1;
    }

    // start DexHand
    if (dh_start_server(ctx) < 0) {
        goto stop;
    }
    // acquire control
    if (dh_acquire_hand(ctx) < 0) {
        goto stop;
    }
    // init position
    if (dh_set_home(ctx, NAN) < 0) {
        goto stop;
    }
    // calibrate force
    if (dh_calibrate_force_zero(ctx) < 0) {
        goto stop;
    }
    // clean error
    if (dh_clear_hand_error(ctx) < 0) {
        goto stop;
    }
    // move to position
    if (dh_pos_goto(ctx, 30.0, NAN, NAN, NAN) < 0) {
        goto stop;
    }
    sleep_sec(1.0);
    // release control
    if (dh_release_hand(ctx) < 0) {
        goto stop;
    }
    // acquire control again
    if (dh_acquire_hand(ctx) < 0) {
        goto stop;
    }
    // move back
    if (dh_set_home(ctx, NAN) < 0) {
        goto stop;
    }

stop:
    // stop (auto release control)
    dh_stop_server(ctx);

    return 0;
}

void
hand_cb(const dexhand_ctx *ctx)
{
    const hand_info *data = dh_get_hand_data(ctx);
    // print data
    if (data->frame_cnt % 10 == 0) {
        printf("[%u] time: %.3lfs, nowpos: %.3fmm\n", data->frame_cnt, data->time, data->now_pos);
    }
}

void
term_cb()
{
    printf("Got signal, exited...\n");
}

// vim:ts=4:et:sw=4
