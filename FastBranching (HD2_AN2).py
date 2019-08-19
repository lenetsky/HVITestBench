# **
# Keysight Confidential
# Copyright Keysight Technologies 2019
#
# @file
# @author hvi team
# **
#

# Fast Branching example compiles and runs HVI sequences in two (or more) PXI modules. the first sequence has a wait for event statement that waits
# for a PXI2 signal to happen. Both sequences are then resynchronized with a junction statement and queue a waveform depending on a register value.
# Here the register WfNum is used to select the waveform to be queued. Another register, named cycleCnt in this example, is used as a counter
# to record the number of received external trigger events.

# This example first opens two SD1 cards (real hardware or simulation mode), creates two HVI modules from the cards, adds a chassis (real hardware or
# simulated), gets the SD1 hvi engines and adds it to the HVI instrument, then adds and configures the trigger used by each sequence, and finally adds
# the instructions in both sequences, compiles, and runs.


#     [moduleList[0]]    [moduleList[1]]
#         Engine             Engine
#         Seq 0              Seq 1
#       +-------+          +-------+
#       | Start |          | Start | / ______
#       +-------+          +-------+ \       |
#           | 10               |             |
#     +------------+           |             |
#     |WaitForEvent|           |             |
#     +------------+           |             |
#           | 10               | 10          |
#      +----------+      +----------+        |
#      | SyncJunc |      | SyncJunc |        |
#      +----------+      +----------+        |
#           | 10               | 10          |
#    +-------------+    +-------------+      |
#    | AWGqueueWFM |    | AWGqueueWFM |      |
#    | with WfNum  |    |  with WfNum |      |
#    +-------------+    +-------------+      |
#           | 2000             | 2000        |
#     +-----------+      +-----------+       |
#     |AWG Trigger|      |AWG Trigger|       |
#     +-----------+      +-----------+       |
#           | 100              |             |
#     +----------+             |             |
#     |cycleCnt++|             | 110         |
#     +----------+             |             |
#           | 10               |             |
#     +----------+       +----------+        |
#     |   Jump   |       |   Jump   |  ------+
#     +----------+       +----------+
#           | 10               | 10
#      +-------+          +-------+
#      |  End  |          |  End  |
#      +-------+          +-------+


import sys
import keysightSD1
import pyhvi
from datetime import timedelta


def main():
    hwSimulated = False

    if hwSimulated:
        options = ",simulated=true"
    elif hwSimulated == False:
        options = ""
    else:
        print("hwSimulated not set to valid value")
        sys.exit()

    # Create module definitions
    moduleDescriptors = [ModuleDescriptor(1, 4, options), ModuleDescriptor(1, 5, options)]

    moduleList = []
    minChassis = 0
    maxChassis = 0

    # Open modules
    for descriptor in moduleDescriptors:
        newModule = keysightSD1.SD_AOU()
        chassisNumber = descriptor.chassisNumber
        id = newModule.openWithSlot("", chassisNumber, descriptor.slotNumber)
        if id < 0:
            print("Error opening module in chassis {}, slot {}, opened with ID: {}".format(descriptor.chassisNumber,
                                                                                           descriptor.slotNumber, id))
            print("Press any key to exit...")
            input()
            sys.exit()

        # Determine what minChassis is based off information in module descriptors
        moduleList.append(newModule)
        if minChassis == 0 or minChassis > chassisNumber:
            minChassis = chassisNumber

        if maxChassis == 0 or maxChassis < chassisNumber:
            maxChassis = chassisNumber

    # Queue waveforms
    for index in range(0, len(moduleList)):
        AWGqueueWfm(moduleList[index])

    # Obtain HVI interface from modules
    moduleHviList = []
    for module in moduleList:
        if not module.hvi:
            print("Module in chassis {} and slot {} does not support HVI2.0... exiting".format(module.getChassis(),
                                                                                               module.getSlot()))
            sys.exit()
        moduleHviList.append(module.hvi)

    ######################################
    ## Configure resources in HVI instance
    ######################################

    # Add engines to the engineList
    engineList = []
    for module in moduleHviList:
        engineList.append(module.engines.master_engine)

    # Create HVI instance
    moduleResourceName = "KtHvi"
    hvi = pyhvi.KtHvi(moduleResourceName)

    # Assign triggers to HVI object to be used for HVI-managed synch, data sharing, etc.
    triggerResources = [pyhvi.TriggerResourceId.PXI_TRIGGER0, pyhvi.TriggerResourceId.PXI_TRIGGER1,
                        pyhvi.TriggerResourceId.PXI_TRIGGER7]
    hvi.platform.sync_resources = triggerResources

    # Assign clock frequences that are outside the set of the clock frequencies of each hvi engine
    nonHVIclocks = [10e6]
    hvi.synchronization.non_hvi_core_clocks = nonHVIclocks

    if engineList.__len__() > 1:
        # Add chassis
        if hwSimulated:
            for chassis in range(minChassis, maxChassis + 1):
                hvi.platform.chassis.add_with_options(chassis, "Simulate=True,DriverSetup=model=M9018B,NoDriver=True")
        else:
            hvi.platform.chassis.add_auto_detect()

        ##### Uncomment for debugging with squidboard
        # for chassis in range(minChassis, maxChassis):
        #     lowSlot = 14
        #     if chassis == minChassis:
        #         lowSlot = 9
        #
        #     hvi.platform.add_squidboards(chassis, lowSlot, chassis + 1, 9)

    # Get engine IDs
    engine_count = 0
    for engineID in engineList:
        hvi.engines.add(engineID, "SdEngine{}".format(engine_count))
        engine_count += 1

    ######################################
    ## Start HVI sequence creation
    ######################################

    print("Press enter to begin creation of the HVI sequence")
    input()

    # Create register cycleCnt in module0, the module waiting for external trigger events
    seq0 = hvi.engines[0].main_sequence
    cycleCnt = seq0.registers.add("cycleCnt", pyhvi.RegisterSize.SHORT)

    # Create a register WfNum in each PXI module. WfNum will be used to queue waveforms
    for index in range(0, hvi.engines.count):
        engine = hvi.engines[index]
        seq = engine.main_sequence
        seq.registers.add("WfNum", pyhvi.RegisterSize.SHORT)

    # Create list of module resources to use in HVI sequence
    waitTrigger = moduleHviList[0].triggers.pxi_2
    hvi.engines[0].events.add(waitTrigger, "extEvent")

    # Add wait statement to first engine sequence (using sequence.programming interface)
    waitEvent = seq0.programming.add_wait_event("wait_external_trigger", 10)
    waitEvent.event = hvi.engines[0].events["extEvent"]
    waitEvent.set_mode(pyhvi.EventDetectionMode.FALLING_EDGE, pyhvi.SyncMode.IMMEDIATE)

    # Add wait trigger just to be sure Pxi from the cards is not interfering Pxi2 triggering from a third card (the trigger the waitEvent is waiting for).
    trigger = hvi.engines[0].triggers.add(waitTrigger, "extTrigger")
    trigger.configuration.direction = pyhvi.Direction.INPUT
    trigger.configuration.trigger_polarity = pyhvi.TriggerPolarity.ACTIVE_HIGH

    # Add global synchronized junction to HVI instance using hvi.programming interface
    junctionName = "GlobalJunction"
    junctionTime_ns = 10
    hvi.programming.add_junction(junctionName, junctionTime_ns)

    # Parameters for AWG queue WFM with register
    startDelay = 0
    nCycles = 1
    prescaler = 0
    nAWG = 0

    # Add actions to HVI engines
    for index in range(0, hvi.engines.count):
        moduleActions = moduleList[index].hvi.actions
        engine = hvi.engines[index]
        engine.actions.add(moduleActions.awg1_start, "awg_start1")
        engine.actions.add(moduleActions.awg2_start, "awg_start2")

        engine.actions.add(moduleActions.awg1_trigger, "awg_trigger1")
        engine.actions.add(moduleActions.awg2_trigger, "awg_trigger2")

    # Add AWG queue waveform and AWG trigger to each module's sequence
    for index in range(0, hvi.engines.count):
        engine = hvi.engines[index]

        # Obtain main sequence from engine to add instructions
        seq = engine.main_sequence

        # Add AWG queue waveform instruction to the sequence
        AwgQueueWfmInstrId = moduleList[index].hvi.instructions.queuewaveform.ID
        AwgQueueWfmId = moduleList[index].hvi.instructions.queuewaveform.parameter.waveform.ID

        instruction0 = seq.programming.add_instruction("awgQueueWaveform", 10, AwgQueueWfmInstrId)
        instruction0.set_parameter(AwgQueueWfmId, seq.registers["WfNum"])
        instruction0.set_parameter(moduleList[index].hvi.instructions.queuewaveform.parameter.channel.ID, nAWG)
        instruction0.set_parameter(moduleList[index].hvi.instructions.queuewaveform.parameter.triggerMode.ID,
                                   keysightSD1.SD_TriggerModes.SWHVITRIG)
        instruction0.set_parameter(moduleList[index].hvi.instructions.queuewaveform.parameter.startDelay.ID, startDelay)
        instruction0.set_parameter(moduleList[index].hvi.instructions.queuewaveform.parameter.Cycles.ID, nCycles)
        instruction0.set_parameter(moduleList[index].hvi.instructions.queuewaveform.parameter.prescaler.ID, prescaler)


        awgTriggerList = [engine.actions["awg_trigger1"], engine.actions[
            "awg_trigger2"]]
        instruction2 = seq.programming.add_instruction("AWG trigger", 2e3,
                                                       hvi.instructions.instructions_action_execute.id)
        instruction2.set_parameter(hvi.instructions.instructions_action_execute.action, awgTriggerList)

    # Increment cycleCnt in module0
    instructionRYinc = seq0.programming.add_instruction("add", 10, hvi.instructions.instructions_add.id)
    instructionRYinc.set_parameter(hvi.instructions.instructions_add.left_operand, 1)
    instructionRYinc.set_parameter(hvi.instructions.instructions_add.right_operand, cycleCnt)
    instructionRYinc.set_parameter(hvi.instructions.instructions_add.result_register, cycleCnt)

    # Global Jump
    jumpName = "jumpStatement"
    jumpTime = 10000
    jumpDestination = "Start"
    hvi.programming.add_jump(jumpName, jumpTime, jumpDestination)

    # Add global synchronized end to close HVI execution (close all sequences - using hvi-programming interface)
    hvi.programming.add_end("EndOfSequence", 100)


    ############################################
    ## Compile and run HVI2.0 virtual instrument
    ############################################


    # Compile the sequence
    hvi.compile()

    # Load the HVI to HW: load sequences, config triggers/events/..., lock resources, etc.
    hvi.load_to_hw()

    print("Press enter to start HVI...")
    input()

    time = timedelta(seconds=0)
    hvi.run(time)

    status = 1
    chassisNumber = 1
    slotNumber = 3
    extTrigModule = keysightSD1.SD_AOU()

    partNumber = ""

    # Connect to trigger module
    status = extTrigModule.openWithSlot(partNumber, chassisNumber, slotNumber)
    if (status < 0):
        print("Invalid Module Name, Chassis or Slot numbers might be invalid! Press enter to quit")
        input()
        sys.exit()

    # initialize register cycleCnt
    seq0.registers["cycleCnt"].write(0)

    wfNum = 1
    nWfm = 2

    # Loop as many times as desired, press q to exit
    while True:
        for index in range(0, hvi.engines.count):
            engine = hvi.engines[index]
            seq = engine.main_sequence
            seq.registers["WfNum"].write(wfNum)

        print("N. of external triggers received at Module0: cycleCnt = {}".format(seq0.registers["cycleCnt"].read()))
        print("Press enter to trigger PXI2, press q to exit")

        key = input()

        if key == 'q':
            break
        else:
            triggerPXI2(extTrigModule)

        # Change wfNum at each iteration
        if (wfNum >= nWfm):  # general case of nWfm
            wfNum = 1
        else:
            wfNum = wfNum + 1

    # Release HVI instance from HW (unlock resources)
    print("Exiting...")
    hvi.release_hw()

    # Close modules
    for module in moduleList:
        module.close()

# Module descriptor class used for initializing instruments
class ModuleDescriptor:
    chassisNumber = 0
    slotNumber = 0
    options = ""

    def __init__(self, chassisNumber, slotNumber, options):
        self.chassisNumber = chassisNumber
        self.slotNumber = slotNumber
        self.options = options

# Function for triggering PXI2
def triggerPXI2(moduleAOU):
    moduleAOU.PXItriggerWrite(keysightSD1.SD_TriggerExternalSources.TRIGGER_PXI2, keysightSD1.SD_TriggerValue.HIGH)
    moduleAOU.PXItriggerWrite(keysightSD1.SD_TriggerExternalSources.TRIGGER_PXI2, keysightSD1.SD_TriggerValue.LOW)
    moduleAOU.PXItriggerWrite(keysightSD1.SD_TriggerExternalSources.TRIGGER_PXI2, keysightSD1.SD_TriggerValue.HIGH)

# Function to queue some waveforms in the AWGs
def AWGqueueWfm(moduleAOU):
    error = 0

    # AWG Settings Variables
    hwVer = moduleAOU.getHardwareVersion()
    if hwVer < 4:
        nAWG = 0
    else:
        nAWG = 1

    # AWG reset
    moduleAOU.AWGstop(nAWG)
    moduleAOU.waveformFlush()
    moduleAOU.AWGflush(nAWG)

    # Set AWG mode
    amplitude = 1.0
    moduleAOU.channelWaveShape(nAWG, keysightSD1.SD_Waveshapes.AOU_AWG)
    moduleAOU.channelAmplitude(nAWG, amplitude)

    # Queue settings
    syncMode = keysightSD1.SD_SyncModes.SYNC_NONE
    queueMode = keysightSD1.SD_QueueMode.ONE_SHOT
    moduleAOU.AWGqueueConfig(nAWG, queueMode)
    moduleAOU.AWGqueueSyncMode(nAWG, syncMode)

    # Create a pulsed waveform
    wfmType = keysightSD1.SD_WaveformTypes.WAVE_ANALOG
    wfmLen = 200
    wfmNum = 1
    wfmNum1 = 2
    onTime = 50
    wfmData = []
    for ii in range(0, wfmLen):
        value = 0.0
        if ii < onTime:
            value = 1.0

        wfmData.append(value)

    wave = keysightSD1.SD_Wave()
    wave.newFromArrayDouble(wfmType, wfmData)
    # wave.newFromFile("C:\\Users\\Public\\Documents\\Keysight\\SD1\\Examples\\Waveforms\\Gaussian.csv")
    error = moduleAOU.waveformLoad(wave, wfmNum)
    if (error < 0):
        print("WaveformLoad0 error ", error)

    # Create a ramp waveform
    wfmData1 = []
    for ii in range(0, wfmLen):
        value = 0.0
        if ii < onTime:
            value = float(ii) / onTime

        wfmData1.append(value)

    wave1 = keysightSD1.SD_Wave()
    wave1.newFromArrayDouble(wfmType, wfmData1)
    # wave1.newFromFile("C:\\Users\\Public\\Documents\\Keysight\\SD1\\Examples\\Waveforms\\Exponential.csv")
    error = moduleAOU.waveformLoad(wave1, wfmNum1)
    if (error < 0):
        print("WaveformLoad1 error ", error)

    moduleAOU.AWGstart(nAWG)


if __name__ == '__main__':
    main()
