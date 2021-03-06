from enum import IntEnum, IntFlag


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


class AxisStatus(IntFlag):
    # Enabled: The axis is enabled.
    Enabled = 2 ** 0
    # Homed: The axis is homed.
    Homed = 2 ** 1
    # In Position: The axis is considered to be in position as configured
    # by the InPositionDistance and InPositionTime parameters.
    InPosition = 2 ** 2
    # Move Active: The axis is performing drive generated motion.
    MoveActive = 2 ** 3
    # Acceleration Phase: The axis is accelerating.
    AccelPhase = 2 ** 4
    # Deceleration Phase: The axis is decelerating.
    DecelPhase = 2 ** 5
    # Position Capture Active: Position capture is armed on the axis and
    # waiting for a trigger signal.
    PositionCapture = 2 ** 6
    # Current Clamp: For piezo drives, the controller clamps the motor
    # output to the value of the PiezoVoltageClampLow or the
    # PiezoVoltageClampHigh parameter. For all other drives, the controller
    # clamps the motor output to the value of the MaxCurrentClamp parameter.
    CurrentClamp = 2 ** 7
    # Brake Output Level: This represents the state of the dedicated
    # brake output.
    BrakeOutput = 2 ** 8
    # Motion Direction (1 = CW): Indicates the direction of the active (or
    # last) motion.
    MotionIsCw = 2 ** 9
    # Gearing or camming active: Gearing or camming is currently active on the
    # axis.
    MasterSlaveControl = 2 ** 10
    # Calibration Active: The correction table for this axis is currently
    # being applied.
    CalActive = 2 ** 11
    # Calibration Enabled: A calibration file contains a calibration table
    # that corrects this axis. The state of this bit is not affected by the
    # CALENABLE or CALDISABLE commands.
    CalEnabled = 2 ** 12
    # Joystick Control: The axis is currently performing motion under control
    # of the JOYSTICK command.
    JoystickControl = 2 ** 13
    # Homing: The axis is currently performing motion as part of the home
    # cycle.
    Homing = 2 ** 14
    # Master Motion Suppressed: The axis position lost synchronization with the
    # master and is ignoring profiled position.
    MasterSuppress = 2 ** 15
    # Gantry Mode Active: This gantry is actively part of a gantry pair.
    GantryActive = 2 ** 16
    # Gantry Master Active: This axis is a gantry master in a gantry pair.
    GantryMaster = 2 ** 17
    # Autofocus Active: This axis is operating under control of the AUTOFOCUS
    # loop.
    AutofocusActive = 2 ** 18
    # Command Shaping Filter Done: The filter defined by the Command
    # Shaping Parameters is complete.
    CommandFilterDone = 2 ** 19
    # In Position 2: The axis is considered to be in position as configured
    # by the InPosition2Distance and InPosition2Time parameters.
    InPosition2 = 2 ** 20
    # Servo Control: The axis is operating under servo control.
    ServoControl = 2 ** 21
    # CW End Of Travel Limit Input Level: This represents the state of
    # the CW end of travel limit input. It is not affected by the active
    # polarity, which is configured by the EndOfTravelLimitSetup parameter.
    CwEOTLimit = 2 ** 22
    # CCW End Of Travel Limit Input Level: This represents the state of
    # the CCW end of travel limit input. It is not affected by the active
    # polarity, which is configured by the EndOfTravelLimitSetup parameter.
    CcwEOTLimit = 2 ** 23
    # Home Limit Input Level: This represents the state of the home limit
    # input. It is not affected by the active polarity, which is configured by
    # the EndOfTravelLimitSetup parameter.
    HomeLimit = 2 ** 24
    # Marker Input Level: This represents the state of the marker input.
    MarkerInput = 2 ** 25
    # Hall A Input Level: This represents the state of the Hall-effect
    # sensor A input.
    HallAInput = 2 ** 26
    # Hall B Input Level: This represents the state of the Hall-effect
    # sensor B input.
    HallBInput = 2 ** 27
    # Hall C Input Level: This represents the state of the Hall-effect
    # sensor C input.
    HallCInput = 2 ** 28
    # Sine Encoder Input Error: An error condition is present on the Sine
    # encoder input of the position feedback device.
    SineEncoderError = 2 ** 29
    # Cosine Encoder Input Error: An error condition is present on the
    # Cosine encoder input of the position feedback device.
    CosineEncoderError = 2 ** 30
    # Emergency Stop Input Level: This represents the state of the
    # emergency stop sense input.
    ESTOPInput = 2 ** 31


class AxisFault(IntFlag):
    # Position Error Fault: The absolute value of the difference between the
    # position command and the position feedback exceeded the threshold
    # specified by the PositionErrorThreshold parameter.
    PositionError = 2 ** 0
    # Over Current Fault: The average motor current exceeded the threshold
    # specified by the AverageCurrentThreshold and AverageCurrentTime
    # parameters.
    OverCurrent = 2 ** 1
    # CW/Positive End-of-Travel Limit Fault: The axis encountered the clockwise
    # (positive) end-of-travel limit switch.
    CwEOTLimit = 2 ** 2
    # CCW/Negative End-of-Travel Limit Fault: The axis encountered the
    # counter-clockwise (negative) end-of-travel limit switch.
    CcwEOTLimit = 2 ** 3
    # CW/High Software Limit Fault: The axis was commanded to move beyond the
    # position specified by the SoftwareLimitHigh parameter.
    CwSoftLimit = 2 ** 4
    # CCW/Low Software Limit Fault: The axis was commanded to move beyond the
    # position specified by the SoftwareLimitLow parameter.
    CcwSoftLimit = 2 ** 5
    # Amplifier Fault: The amplifier for this axis exceeded its maximum current
    # rating or experienced an internal error.
    AmplifierFault = 2 ** 6
    # Position Feedback Fault: The drive detected a problem with the feedback
    # device specified by the PositionFeedbackType and PositionFeedbackChannel
    # parameters.
    PositionFbk = 2 ** 7
    # Velocity Feedback Fault: The drive detected a problem with the feedback
    # device specified by the VelocityFeedbackType and VelocityFeedbackChannel
    # parameters.
    VelocityFbk = 2 ** 8
    # Hall Sensor Fault: The drive detected an invalid state (all high or all
    # low) for the Hall-effect sensor inputs on this axis.
    HallFault = 2 ** 9
    # Maximum Velocity Command Fault: The commanded velocity is more than the
    # velocity command threshold. Before the axis is homed, this threshold is
    # specified by the VelocityCommandThresholdBeforeHome parameter. After the
    # axis is homed, this threshold is specified by the
    # VelocityCommandThreshold parameter.
    MaxVelocity = 2 ** 10
    # Emergency Stop Fault: The emergency stop sense input, specified by the
    # ESTOPFaultInput parameter, was triggered.
    EstopFault = 2 ** 11
    # Velocity Error Fault: The absolute value of the difference between the
    # velocity command and the velocity feedback exceeded the threshold
    # specified by the VelocityErrorThreshold parameter.
    VelocityError = 2 ** 12
    # External Fault: The external fault input, specified by the
    # ExternalFaultAnalogInput or ExternalFaultDigitalInput parameters, was
    # triggered.
    ExternalFault = 2 ** 15
    # Motor Temperature Fault: The motor thermistor input was triggered, which
    # indicates that the motor exceeded its maximum recommended operating
    # temperature.
    MotorTemp = 2 ** 17
    # Amplifier Temperature Fault: The amplifier exceeded its maximum
    # recommended operating temperature.
    AmplifierTemp = 2 ** 18
    # Encoder Fault: The encoder fault input on the motor feedback connector
    # was triggered.
    EncoderFault = 2 ** 19
    # Communication Lost Fault: One or more of the drives on the network lost
    # communications with the controller.
    CommLost = 2 ** 20
    # Feedback Scaling Fault: The difference between the position feedback and
    # the scaled (adjusted by GainKv) velocity feedback exceeds the threshold
    # specified by the PositionErrorThreshold parameter.
    FbkScalingFault = 2 ** 23
    # Marker Search Fault: The distance that the axis moved while searching for
    # the marker exceeded the threshold specified by the MarkerSearchThreshold
    # parameter.
    MrkSearchFault = 2 ** 24
    # Voltage Clamp Fault: The commanded voltage output exceeded the value of
    # the PiezoVoltageClampLow or PiezoVoltageClampHigh parameter.
    VoltageClamp = 2 ** 27
    # Power Supply Fault: The power supply output has exceeded the allowable
    # power or temperature threshold.
    PowerSupply = 2 ** 28
    # Internal Fault: The drive failed has encountered an internal error and
    # had to disable. For assistance, contact Aerotech Customer Service.
    Internal = 2 ** 30


EOS_CHAR = '\n'
ACK_CHAR = '%'
NAK_CHAR = '!'
FAULT_CHAR = '#'
TIMEOUT_CHAR = '$'
