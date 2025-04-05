// tac3d.cpp
// Tac3D reading example
//
// copyright (C) 2024 - 2024 by pingplug
//
#include "dexhand_client.h"
#include "libTac3D.hpp"

#include <stdio.h>

// callback functions
void hand_cb(const dexhand_ctx *ctx);
void Tac3DRecvCallback(Tac3D::Frame &frame, void *param);

// struct for storing Tac3D data
struct Tac3D_info {
    std::string SN;
    uint32_t    frameIndex;
    double      sendTimestamp;
    double      recvTimestamp;
    cv::Mat     P;
    cv::Mat     D;
    cv::Mat     F;
    cv::Mat     Fr;
    cv::Mat     Mr;

    Tac3D_info(std::string _SN)
    {
        SN         = _SN;
        frameIndex = 0xFFFFFFFF;
    }
};

Tac3D_info tacinfo1("HDL1-0001");
Tac3D_info tacinfo2("HDL1-0002");

std::map<std::string, Tac3D_info *> tac_dict;

int
main()
{
    // set log level
    dh_set_log("log.txt", DH_LL_DBG);
    // init context
    dexhand_ctx *ctx;
    if (dh_dexhand_client(&ctx, "192.168.2.100", 60031, NULL, hand_cb) < 0) {
        printf("Can not init context, exit\n");
        return -1;
    }
    // add to dict
    tac_dict.insert({ tacinfo1.SN, &tacinfo1 });
    tac_dict.insert({ tacinfo2.SN, &tacinfo2 });
    // init Tac3D
    auto tac3d = Tac3D::Sensor(Tac3DRecvCallback, 9988, NULL);
    // start DexHand
    if (dh_start_server(ctx) < 0) {
        goto stop;
    }
    // acquire control
    if (dh_acquire_hand(ctx) < 0) {
        goto stop;
    }
    // position zero point
    if (dh_set_home(ctx, NAN) < 0) {
        goto stop;
    }
    // force zero point
    if (dh_calibrate_force_zero(ctx) < 0) {
        goto stop;
    }
    // send calibrate signal to all Tac3D
    for (auto &pair : tac_dict) {
        tac3d.calibrate(pair.first);
    }
    // contact
    if (dh_contact(ctx, 8.0, 2.0, 15.0, 10.0) < 0) {
        goto stop;
    }
    // apply grasp force
    if (dh_grasp(ctx, 5.0, 5.0) < 0) {
        goto stop;
    }
    // release control
    if (dh_release_hand(ctx) < 0) {
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
    // get pointer
    const hand_info *data = dh_get_hand_data(ctx);
    // check if we get tacinfo
    if (tacinfo1.frameIndex == 0xFFFFFFFF || tacinfo2.frameIndex == 0xFFFFFFFF) {
        return;
    }
    // print data
    if (data->frame_cnt % 10 == 0) {
        printf("Error:{%s}, nowforce1: %.3fN nowforce2: %.3fN nowTacFz1: %.3fN nowTacFz2: %.3fN nowpos: %.3fmm\n",
               data->error_flag == DH_TRUE ? "True" : "False", data->now_force[0], data->now_force[1],
               tacinfo1.Fr.at<double>(0, 2), tacinfo2.Fr.at<double>(0, 2), data->now_pos);
    }
}

// disable unused parameter check
// reason: used for function pointer
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-parameter"

void
Tac3DRecvCallback(Tac3D::Frame &frame, void *param)
{
    cv::Mat *tempMat;

    // get the SN code, which can be used to distinguish which Tac3D sensor the tactile information comes from
    std::string SN = frame.SN;

    // check SN in dict
    if (tac_dict.find(SN) == tac_dict.end()) {
        return;
    }

    // get data struct from SN
    auto tacinfo = tac_dict[SN];

    // get the frame index
    tacinfo->frameIndex = frame.index;

    // get the timestamp
    tacinfo->sendTimestamp = frame.sendTimestamp;
    tacinfo->recvTimestamp = frame.recvTimestamp;

    // Use the frame.get function to obtain the data pointer of the 3D shape of the cv::Mat type through the data name
    // "3D_Positions" The three columns of the matrix are the components in the x, y, and z directions, respectively
    // Each row of the matrix corresponds to a sensing point
    tempMat = frame.get<cv::Mat>("3D_Positions");
    // When the Tac3DRecvCallback function returns, the frame's memory may be reclaimed. If you need to use the acquired
    // data elsewhere, you need to use the "copyTo" function to copy the data to another place.
    tempMat->copyTo(tacinfo->P);

    // Use the frame.get function to obtain the data pointer of the displacement field of the cv::Mat type through the
    // data name "3D_Displacements" The three columns of the matrix are the components in the x, y, and z directions,
    // respectively Each row of the matrix corresponds to a sensing point
    tempMat = frame.get<cv::Mat>("3D_Displacements");
    tempMat->copyTo(tacinfo->D);

    // Use the frame.get function to obtain the data pointer of the distributed force of the cv::Mat type through the
    // data name "3D_Forces" The three columns of the matrix are the components in the x, y, and z directions,
    // respectively Each row of the matrix corresponds to a sensing point
    tempMat = frame.get<cv::Mat>("3D_Forces");
    tempMat->copyTo(tacinfo->F);

    // Use the frame.get function to obtain the data pointer of the resultant force of the cv::Mat type through the data
    // name "3D_ResultantForce" The three columns of the matrix are the components in the x, y, and z directions,
    // respectively
    tempMat = frame.get<cv::Mat>("3D_ResultantForce");
    tempMat->copyTo(tacinfo->Fr);

    // Use the frame.get function to obtain the data pointer of the resultant moment of the cv::Mat type through the
    // data name "3D_ResultantMoment" The three columns of the matrix are the components in the x, y, and z directions,
    // respectively
    tempMat = frame.get<cv::Mat>("3D_ResultantMoment");
    tempMat->copyTo(tacinfo->Mr);
}

// end: disable unused parameter check
#pragma GCC diagnostic pop

// vim:ts=4:et:sw=4
