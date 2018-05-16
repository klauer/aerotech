from enum import IntEnum


class Drives(IntEnum):
    Ensemble = 0x0800
    CP = 0X8005
    MP = 0X8006
    EPAQ = 0X8007
    CL = 0X8008
    HPE = 0X8009
    HLE = 0X800A
    ML = 0X800B
    PMT = 0X800C
    LAB = 0X800D
    QLAB = 0X800E


class Commands(IntEnum):
    done = 0
    velocity_on = 1
    velocity_off = 2
    halt = 3
    start = 4
    pvt_init_time_abs = 5
    pvt_init_time_inc = 6
    pvt1 = 7
    pvt2 = 8
    pvt3 = 9
    pvt = 10
    abort = 11
    start_abort = 12

    scope_buffer = 13
    scope_data = 14
    scope_status = 15
    scope_trigger = 16
    scope_trigger_period = 17
    drive_info = 18
    linear = 19
    daq_trigger = 20
    daq_input = 21
    daq_on = 22
    daq_off = 23
    daq_read = 24
    do_trajectory = 25

    # new commands beyond original doCommand.ab:
    fast_scope_data = 26


class ScopeStatusType(IntEnum):  # intmask
    max_points = 0
    points_allocated = 1
    points_collected = 2
    collection_status = 3


class DataCollectionMask(IntEnum):  # intmask
    allocated = 1 << 0
    active = 1 << 1
    triggered = 1 << 2
    done = 1 << 3
    aborted = 1 << 4
    overflow = 1 << 5
    trigger_initiated = 1 << 6


class Variables(IntEnum):
    command = 45
    int_arg1 = 46
    int_arg2 = 47
    int_arg3 = 48
    int_arg4 = 49
    double_arg1 = 1
    double_arg2 = 2
    double_arg3 = 3
    double_arg4 = 4
    double_arg5 = 5
    double_arg6 = 6
    double_arg7 = 7
    double_arg8 = 8
    double_arg9 = 9
    num_int_args = 44
    num_double_args = 43
    pvt_wait_ms = 42


class ScopeData(IntEnum):
    position_command = 0
    position_feedback = 1
    external_position = 2
    axis_fault = 3
    axis_status = 4
    analog_input0 = 5
    analog_input1 = 6
    analog_output0 = 7
    analog_output1 = 8
    digital_input0 = 9
    digital_input1 = 10
    digital_output0 = 11
    digital_output1 = 12
    current_command = 13
    current_feedback = 14
    optional_data1 = 15
    optional_data2 = 16
    program_counter = 17


class TaskState(IntEnum):
    unknown = 0
    idle = 1
    ready = 2
    running = 3
    paused = 4
    done = 5
    errored = 6


EOS_CHAR = '\n'
ACK_CHAR = '%'
NAK_CHAR = '!'
FAULT_CHAR = '#'
TIMEOUT_CHAR = '$'
