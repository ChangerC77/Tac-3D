// dexhand_client.h
//
// copyright (C) 2024 - 2024 by pingplug
//
#pragma once

#include <stdint.h>

// for symbol attribute
#ifdef _WIN32
#ifdef CDH_DLL
#define CDH_EXPORT __declspec(dllexport)
#else // CDH_DLL
#define CDH_EXPORT __declspec(dllimport)
#endif // CDH_DLL
#else  // _WIN32
#ifdef CDH_DLL
#define CDH_EXPORT __attribute__((visibility("protected")))
#else // CDH_DLL
#define CDH_EXPORT
#endif // CDH_DLL
#endif // _WIN32

#define TASK_STR_SIZE 16

#ifdef __cplusplus
extern "C" {
#endif

// enumeration typedef
/// bool type
typedef enum {
    /// false
    DH_FALSE = 0,
    /// true
    DH_TRUE = 1,
    /// default value for input
    DH_DEFAULT = 2,
} DH_BOOL;

/// log level
typedef enum {
    /// print nothing
    DH_LL_NONE = 0,
    /// print error only
    DH_LL_ERROR = 1,
    /// print error and warning
    DH_LL_WARN = 2,
    /// print error, warning and info
    DH_LL_INFO = 3,
    /// print error, warning, info and debug
    DH_LL_DBG = 4,
    /// print error, warning, info, debug and verbose
    DH_LL_VERB = 5,
} DH_LL;

// struct typedef
/// DexHand data
typedef struct {
    /// data counter
    uint32_t frame_cnt;
    /// data time from sender
    double time;
    /// gripper position
    double now_pos;
    /// gripper goal position
    double goal_pos;
    /// gripper speed
    double now_speed;
    /// gripper goal speed
    double goal_speed;
    /// gripper motor current
    double now_current;
    /// gripper goal motor current
    double goal_current;
    /// finger force
    double now_force[2];
    /// gripper force
    double avg_force;
    /// gripper goal force
    double goal_force;
    /// contact stiffness
    double stiffness;
    /// acceleration from IMU
    double imu_acc[3];
    /// angular speed from IMU
    double imu_gyr[3];
    /// if DH_TRUE, the finger is contacted
    DH_BOOL is_contact[2];
    /// the current task name
    char now_task[TASK_STR_SIZE];
    /// the last task name
    char recent_task[TASK_STR_SIZE];
    /// the last task status
    char recent_task_status[TASK_STR_SIZE];
    /// the internal error in DexHand
    DH_BOOL error_flag;
} hand_info;

/// DexHand context
typedef struct dexhand_ctx dexhand_ctx;

// function pointer typedef
/// callback fnction called after received data from DexHand
typedef void (*data_callback)(const dexhand_ctx *ctx);
/// callback fnction called when got Ctrl-C signal
typedef void (*term_callback)(void);

// function prototype
// context
/**
 *  Set log file and log level. If run more than once, the setting will be override.
 *
 *  WARNING: `DH_LL_VERB` log level will generate tons of log and may affect the preformance
 *
 *  @param[in]  fn          name of new log file (the parameter will be ignored if set to NULL)
 *  @param[in]  log_level   level of log, see DH_LL
 *  @return return 0 if no error
 */
CDH_EXPORT int32_t dh_set_log(const char *fn, DH_LL log_level);

/**
 *  Init context, connect to DexHand.
 *
 *  @param[out] ctx context
 *  @param[in]  ip          IP address of DexHand
 *  @param[in]  port        port of DexHand
 *  @param[in]  term_cb     term callback function, set NULL will ignore
 *  @param[in]  hand_cb     DexHand callback function, set NULL will ignore
 *  @return return 0 if no error
 */
CDH_EXPORT int32_t dh_dexhand_client(dexhand_ctx **ctx, const char *ip, uint16_t port, const term_callback term_cb,
                                     const data_callback hand_cb);

/**
 *  Set callback function to context. The callback will be called when got a system signal.
 *  When got signal, `dh_halt()`, `dh_release_hand()` and `dh_release_ctx()` will be called before callback.
 *
 *  The signal caught in Linux system: `SIGHUP`, `SIGINT` and `SIGTERM`.
 *  The event caught in Windows system: `CTRL_C_EVENT`, `CTRL_BREAK_EVENT` and `CTRL_CLOSE_EVENT`.
 *  The signal is triggerd when:
 *  1. Ctrl-C from keyboard.
 *  2. Close the console window.
 *  3. Stop the process from task manager.
 *
 *  For linux user who want to run this in the background after log off, please use `nohup` to disbale `SIGHUP`.
 *
 *  @param[in,out]  ctx     context
 *  @param[in]  callback    callback function, set NULL to unset
 *  @return return 0 if no error
 */
CDH_EXPORT int32_t dh_set_term_callback(dexhand_ctx *ctx, const term_callback callback);

/**
 *  Set hand data callback function to context. The callback will be called when hand data is received.
 *
 *  @param[in,out]  ctx     context
 *  @param[in]  callback    callback function, set NULL to unset
 *  @return return 0 if no error
 */
CDH_EXPORT int32_t dh_set_hand_callback(dexhand_ctx *ctx, const data_callback callback);

// server
/**
 *  Start DexHand server.
 *
 *  @param[in,out]  ctx context
 *  @return return 0 if no error
 */
CDH_EXPORT int32_t dh_start_server(dexhand_ctx *ctx);

/**
 *  Stop DexHand server. Will call `dh_halt()` and `dh_release_hand()` internally.
 *
 *  @param[in,out]  ctx context
 *  @return return 0 if no error
 */
CDH_EXPORT int32_t dh_stop_server(dexhand_ctx *ctx);

// hand
/**
 *  Obtain the control access of DexHand hardware. If the DexHand has not initialized, this function will initialize
 *  DexHand hardware. The DexHand will find its position zero point and calibrate force sensor. Note that before
 *  initialization, other hand commands will be IGNORED by the server.
 *
 *  This function may fail if other client is controlling. In that case, the client controlling DexHand should release
 *  DexHand control access first.
 *
 *  @param[in,out]  ctx context
 *  @return return 0 if no error
 */
CDH_EXPORT int32_t dh_acquire_hand(dexhand_ctx *ctx);

/**
 *  Find DexHand's gripper zero point.
 *
 *  @param[in,out]  ctx context
 *  @param[in]  goal_speed  set home goal speed (in mm/s), set NAN to use default value
 *  @return return 0 if no error
 */
CDH_EXPORT int32_t dh_set_home(dexhand_ctx *ctx, double goal_speed);

/**
 *  Calibrate DexHand's 1D force sensors' zero points.
 *
 *  @param[in,out]  ctx context
 *  @return return 0 if no error
 */
CDH_EXPORT int32_t dh_calibrate_force_zero(dexhand_ctx *ctx);

/**
 *  Close DexHand's fingers until they contact an object. The function will not return until DexHand has indeed
 *  contacted an object and set contact force to `preload_force`. For a quicker contact, you can specified
 *  `quick_move_pos` and `quick_move_speed` so that the gripper will move to `quick_move_pos` in `quick_move_speed`
 *  first then try to contact an object in `contact_speed`.
 *
 *  @param[in,out]  ctx context
 *  @param[in]  contact_speed   contact goal speed (in mm/s), set NAN to use default value
 *  @param[in]  preload_force   the force needed when the function return (in N), set NAN to use default value
 *  @param[in]  quick_move_speed    the moving speed when a quick approach is needed (in mm/s). Must be specified with
 *                                  `quick_move_pos` at the same time, set NAN to use default value
 *  @param[in]  quick_move_pos  the terminal pos of quick approach (in mm). Must be specified with `quick_move_speed` at
 *                              the same time, set NAN to use default value
 *  @return return 0 if no error
 */
CDH_EXPORT int32_t dh_contact(dexhand_ctx *ctx, double contact_speed, double preload_force, double quick_move_speed,
                              double quick_move_pos);

/**
 *  Control the grasping force of DexHand. A linear time-dependent force planning is applied before sending to the
 *  driver.
 *
 *  Before control, DexHand must has contact an object. If not, this function will first make it contact. The function
 *  will not return until the desired force is reached.
 *
 *  During preloading, the stiffness will be estimated and used in force control.
 *
 *  @param[in,out]  ctx context
 *  @param[in]  goal_force  desired preload force (in N), set NAN to use default value
 *  @param[in]  load_time   time to load (in s). If set to 0, it means a step signal, set NAN to use default value
 *  @return return 0 if no error
 */
CDH_EXPORT int32_t dh_grasp(dexhand_ctx *ctx, double goal_force, double load_time);

/**
 *  Control the grasping force of DexHand. It's a non-blocking version of `dh_grasp()`. There are no force planning, the
 *  goal_force will be send to the driver directly.
 *
 *  Before control, DexHand must has contact an object. If not, this function will first make it contact. The function
 *  will not return until the desired force is reached.
 *
 *  During preloading, the stiffness will be estimated and used in force control.
 *
 *  @param[in,out]  ctx context
 *  @param[in]  goal_force  desired preload force (in N)
 *  @return return 0 if no error
 */
CDH_EXPORT int32_t dh_force_servo(dexhand_ctx *ctx, double goal_force);

/**
 *  Move DexHand's gripper to appointed position. If the contact force exceed `max_f`, the gripper will stop immediately
 *  with motor maximum deceleration (160 mm/s^2).
 *
 *  @param[in,out]  ctx context
 *  @param[in]  goal_pos    the assigned position (in mm)
 *  @param[in]  max_speed   the maximum absolute speed assigned to the gripper when moving (in mm/s), set NAN to use
 * default value
 *  @param[in]  max_acc the maximum acceleration assigned to the gripper when moving (in mm/s^2), set NAN to use default
 * value
 *  @param[in]  max_f   the maximum force that is allowed when moving (in N), set NAN to use default value
 *  @return return 0 if no error
 */
CDH_EXPORT int32_t dh_pos_goto(dexhand_ctx *ctx, double goal_pos, double max_speed, double max_acc, double max_f);

/**
 *  Move DexHand's gripper to appointed position. It's a non-blocking version of `dh_goto()`. If the contact force
 *  exceed `max_f`, the gripper will stop immediately with motor maximum deceleration(160 mm/s^2).
 *
 *  @param[in,out]  ctx context
 *  @param[in]  goal_pos    the assigned position (in mm)
 *  @param[in]  max_f   the maximum force that is allowed when moving (in N), set NAN to use default value
 *  @return return 0 if no error
 */
CDH_EXPORT int32_t dh_pos_servo(dexhand_ctx *ctx, double goal_pos, double max_f);

/**
 *  Stop the gripper. Can interrupt all hand movement command. This command will clean all unfinished task in queue.
 *  This command can be send by ANY client.
 *
 *  @param[in,out]  ctx context
 *  @return return 0 if no error
 */
CDH_EXPORT int32_t dh_halt(dexhand_ctx *ctx);

/**
 *  When DexHand is in error, call this function to try to clear error. DexHand will not accept any other command until
 *  the error is cleared.
 *
 *  Use hand_info.error_flag to check if DexHand is in error.
 *
 *  @param[in,out]  ctx context
 *  @return return 0 if no error
 */
CDH_EXPORT int32_t dh_clear_hand_error(dexhand_ctx *ctx);

/**
 *  Release the control of DexHand. Then other client can call `dh_acquire_hand()` to acquire control.
 *
 *  @param[in,out]  ctx context
 *  @return return 0 if no error
 */
CDH_EXPORT int32_t dh_release_hand(dexhand_ctx *ctx);

// data
/**
 *  get hand data pointer from context, do not free the pointer.
 *
 *  @param[in]  ctx context
 *  @return     pointer of data struct for hand
 */
CDH_EXPORT const hand_info *dh_get_hand_data(const dexhand_ctx *ctx);

#ifdef __cplusplus
}
#endif

// vim:ts=4:et:sw=4
