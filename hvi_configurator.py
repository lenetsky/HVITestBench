import sys
sys.path.append('C:/Program Files (x86)/Keysight/SD1/Libraries/Python')
import keysightSD1
import pyhvi

# This is a switch that will route to the correct function to configure a given Test object's HVI sequence
def configure_hvi(Test_obj, filestr=""):
    if Test_obj.test_key == "helloworld":
        _helloworld_hvi_configurator(Test_obj)
    elif Test_obj.test_key == "helloworldmimo":
        _helloworldmimo_hvi_configurator(Test_obj)
    elif Test_obj.test_key== "mimoresync":
        _mimoresync_hvi_configurator(Test_obj)
    elif Test_obj.test_key == "fastbranching":
        _fast_branching_hvi_configurator(Test_obj)
    else:
        print("[ERROR] hvi_configurator.configure_HVI: Test object's test_key variable did not match a valid key")

def _helloworld_hvi_configurator(Test_obj):
    # Create SD_AOUHvi object from SD module

    for mod_inst in Test_obj.module_instances:

        module = mod_inst[0]

        sd_hvi = module.hvi

        if not sd_hvi:
            print('Module in CHASSIS {}, SLOT {} does not support HVI2'.format(mod_inst[2][0], mod_inst[2][1]))
            print("Press enter to exit.")
            input()
            sys.exit()

        # Get engine from SD module's SD_AOUHvi object
        sd_engine_aou = sd_hvi.engines.main_engine

        # Create KtHvi instance
        module_resource_name = 'KtHvi'
        hvi = pyhvi.KtHvi(module_resource_name)
        print("HVI instance: ...".format(hvi))

        # Add SD HVI engine to KtHvi instance
        engine = hvi.engines.add(sd_engine_aou, 'SdEngine1')
        print("hvi engine: {}...".format(engine))

        # Configure the trigger used by the sequence
        sequence_trigger = engine.triggers.add(sd_hvi.triggers.front_panel_1, 'SequenceTrigger')
        sequence_trigger.configuration.direction = pyhvi.Direction.OUTPUT
        sequence_trigger.configuration.polarity = pyhvi.TriggerPolarity.ACTIVE_LOW
        sequence_trigger.configuration.delay = 0
        sequence_trigger.configuration.trigger_mode = pyhvi.TriggerMode.LEVEL
        sequence_trigger.configuration.pulse_length = 250

        # *******************************
        # Start KtHvi sequences creation

        sequence = engine.main_sequence  # Obtain main squence from the created HVI instrument

        instruction1 = sequence.programming.add_instruction('TriggerOn', 100,
                                                            hvi.instructions.trigger_write.id)  # Add trigger write instruction to the sequence
        instruction1.set_parameter(hvi.instructions.trigger_write.trigger,
                                   sequence_trigger)  # Specify which trigger is going to be used
        instruction1.set_parameter(hvi.instructions.trigger_write.sync_mode,
                                   pyhvi.SyncMode.IMMEDIATE)  # Specify synchronization mode
        instruction1.set_parameter(hvi.instructions.trigger_write.value,
                                   pyhvi.TriggerValue.ON)  # Specify trigger value that is going to be applied

        instruction2 = sequence.programming.add_instruction('TriggerOff', 1000,
                                                            hvi.instructions.trigger_write.id)  # Add trigger write instruction to the sequence
        instruction2.set_parameter(hvi.instructions.trigger_write.trigger,
                                   sequence_trigger)  # Specify which trigger is going to be used
        instruction2.set_parameter(hvi.instructions.trigger_write.sync_mode,
                                   pyhvi.SyncMode.IMMEDIATE)  # Specify synchronization mode
        instruction2.set_parameter(hvi.instructions.trigger_write.value,
                                   pyhvi.TriggerValue.OFF)  # Specify trigger value that is going to be applied

        hvi.programming.add_end('EndOfSequence', 10)  # Add the end statement at the end of the sequence

        # Assign triggers to HVI object to be used for HVI-managed synchronization, data sharing, etc
        trigger_resources = [pyhvi.TriggerResourceId.PXI_TRIGGER0, pyhvi.TriggerResourceId.PXI_TRIGGER1]
        hvi.platform.sync_resources = trigger_resources

        Test_obj.hvi_instances.append(hvi)

        print("Configured HVI for helloworld test")

def _helloworldmimo_hvi_configurator(Test_obj):

    # Obtain SD_AOUHvi interface from modules
    module_hvi_list = []
    for module in Test_obj.module_instances:
        if not module[0].hvi:
            raise Exception(f'Module in chassis {module[2][0]} and slot {module[2][1]} does not support HVI2')
        module_hvi_list.append(module[0].hvi)

    # Create list of triggers to use in KtHvi sequence
    trigger_list = []
    for mod in module_hvi_list:
        trigger_list.append(mod.triggers.front_panel_1)

    # Create KtHvi instance
    module_resource_name = 'KtHvi'
    Test_obj.hvi = pyhvi.KtHvi(module_resource_name)

    # *********************************
    # Config resource in KtHvi instance

    # Add chassis to KtHvi instance
    Test_obj.hvi.platform.chassis.add_auto_detect()

    # Get engine IDs from module's SD_AOUHvi interface and add each engine to KtHvi instance
    engine_index = 0
    for module_hvi in module_hvi_list:
        sd_engine = module_hvi.engines.main_engine
        Test_obj.hvi.engines.add(sd_engine, f'SdEngine{engine_index}')
        engine_index += 1

    # Configure the trigger used by the sequence
    for index in range(0, Test_obj.hvi.engines.count):
        engine = Test_obj.hvi.engines[index]

        trigger = engine.triggers.add(trigger_list[index], 'SequenceTrigger')
        trigger.configuration.direction = pyhvi.Direction.OUTPUT
        trigger.configuration.drive_mode = pyhvi.DriveMode.PUSH_PULL
        trigger.configuration.polarity = pyhvi.TriggerPolarity.ACTIVE_LOW
        trigger.configuration.delay = 0
        trigger.configuration.trigger_mode = pyhvi.TriggerMode.LEVEL
        trigger.configuration.pulse_length = 250

    # *******************************
    # Start KtHvi sequences creation

    for index in range(0, Test_obj.hvi.engines.count):
        # Get engine in the KtHvi instance
        engine = Test_obj.hvi.engines[index]

        # Obtain main sequence from engine to add instructions
        sequence = engine.main_sequence

        # Add instructions to specific sequence (using sequence.programming interface)
        instruction1 = sequence.programming.add_instruction('TriggerOn', 10,
                                                            Test_obj.hvi.instructions.trigger_write.id)  # Add trigger write instruction to the sequence
        instruction1.set_parameter(Test_obj.hvi.instructions.trigger_write.trigger,
                                   engine.triggers['SequenceTrigger'])  # Specify which trigger is going to be used
        instruction1.set_parameter(Test_obj.hvi.instructions.trigger_write.sync_mode,
                                   pyhvi.SyncMode.IMMEDIATE)  # Specify synchronization mode
        instruction1.set_parameter(Test_obj.hvi.instructions.trigger_write.value,
                                   pyhvi.TriggerValue.ON)  # Specify trigger value that is going to be applyed

        instruction2 = sequence.programming.add_instruction('TriggerOff', 500,
                                                            Test_obj.hvi.instructions.trigger_write.id)  # Add trigger write instruction to the sequence
        instruction2.set_parameter(Test_obj.hvi.instructions.trigger_write.trigger,
                                   engine.triggers['SequenceTrigger'])  # Specify which trigger is going to be used
        instruction2.set_parameter(Test_obj.hvi.instructions.trigger_write.sync_mode,
                                   pyhvi.SyncMode.IMMEDIATE)  # Specify synchronization mode
        instruction2.set_parameter(Test_obj.hvi.instructions.trigger_write.value,
                                   pyhvi.TriggerValue.OFF)  # Specify trigger value that is going to be applyed

    # Add global synchronized end to close KtHvi execution (close all sequences - using hvi-programming interface)
    Test_obj.hvi.programming.add_end('EndOfSequence', 10)

    # Assign triggers to KtHvi object to be used for HVI-managed synchronization, data sharing, etc
    Test_obj.hvi.platform.sync_resources = [pyhvi.TriggerResourceId.PXI_TRIGGER0, pyhvi.TriggerResourceId.PXI_TRIGGER1]

    print("Configured HVI for helloworldmimo test")


def _mimoresync_hvi_configurator(Test_obj):

    # Obtain SD_AOUHvi interface from modules
    module_hvi_list = []
    for module in Test_obj.module_instances:
        if not module[0].hvi:
            raise Exception(f'Module in chassis {module[2][0]} and slot {module[2][1]} does not support HVI2')
        module_hvi_list.append(module[0].hvi)

    # Create lists of triggers to use in KtHvi sequence
    wait_trigger = module_hvi_list[Test_obj.master_module_index].triggers.pxi_2
    trigger_list = []
    engine_list = []
    for module in module_hvi_list:
        trigger_list.append(module.triggers.front_panel_1)
        engine_list.append(module.engines.main_engine)

    # Create KtHvi instance
    module_resource_name = 'KtHvi'
    Test_obj.hvi = pyhvi.KtHvi(module_resource_name)

    # *********************************
    # Config resource in KtHvi instance

    Test_obj.hvi.platform.chassis.add_auto_detect()

    #TODO: need to implement this portion
    # interconnects = hvi.platform.interconnects
    # interconnects.add_squidboards(1, 9, 2, 9)
    # interconnects.add_squidboards(2, 14, 3, 9)
    # interconnects.add_squidboards(3, 14, 4, 9)

    # Add each engine to KtHvi instance
    engine_index = 0
    for engine in engine_list:
        Test_obj.hvi.engines.add(engine, f'SdEngine{engine_index}')
        engine_index += 1

    # Add wait trigger just to be sure Pxi from the cards is not interfering Pxi2 triggering from a third card (the trigger the waitEvent is waiting for).
    start_trigger = Test_obj.hvi.engines[Test_obj.master_module_index].triggers.add(wait_trigger, 'StartTrigger')
    start_trigger.configuration.direction = pyhvi.Direction.INPUT
    start_trigger.configuration.polarity = pyhvi.TriggerPolarity.ACTIVE_LOW

    # Add start event
    start_event = Test_obj.hvi.engines[Test_obj.master_module_index].events.add(wait_trigger, 'StartEvent')

    for index in range(0, Test_obj.hvi.engines.count):
        # Get engine in the KtHvi instance
        engine = Test_obj.hvi.engines[index]

        # Add trigger to engine
        trigger = engine.triggers.add(trigger_list[index], 'PulseOut')
        trigger.configuration.direction = pyhvi.Direction.OUTPUT
        trigger.configuration.drive_mode = pyhvi.DriveMode.PUSH_PULL
        trigger.configuration.polarity = pyhvi.TriggerPolarity.ACTIVE_LOW
        trigger.configuration.delay = 0
        trigger.configuration.trigger_mode = pyhvi.TriggerMode.LEVEL
        trigger.configuration.pulse_length = 250

    # *******************************
    # Start KtHvi sequences creation

    # Add wait statement to first engine sequence (using sequence.programming interface)
    engine_aou1_sequence = Test_obj.hvi.engines[Test_obj.master_module_index].main_sequence
    wait_event = engine_aou1_sequence.programming.add_wait_event('wait external_trigger', 10)
    wait_event.event = Test_obj.hvi.engines[Test_obj.master_module_index].events['StartEvent']
    wait_event.set_mode(pyhvi.EventDetectionMode.ACTIVE,
                        pyhvi.SyncMode.IMMEDIATE)  # Configure event detection and synchronization modes

    # Add global synchronized junction to HVI instance (to all sequences!!! - using hvi.programming interface)
    global_junction = 'GlobalJunction'
    junction_time_ns = 100
    Test_obj.hvi.programming.add_junction(global_junction, junction_time_ns)

    for index in range(0, Test_obj.hvi.engines.count):
        # Get engine in the KtHvi instance
        engine = Test_obj.hvi.engines[index]

        # Obtain main sequence from engine to add instructions
        sequence = engine.main_sequence

        # Add instructions to specific sequence (using sequence.programming interface)
        instruction1 = sequence.programming.add_instruction('TriggerOn', 10,
                                                            Test_obj.hvi.instructions.trigger_write.id)  # Add trigger write instruction to the sequence
        instruction1.set_parameter(Test_obj.hvi.instructions.trigger_write.trigger,
                                   engine.triggers['PulseOut'])  # Specify which trigger is going to be used
        instruction1.set_parameter(Test_obj.hvi.instructions.trigger_write.sync_mode,
                                   pyhvi.SyncMode.IMMEDIATE)  # Specify synchronization mode
        instruction1.set_parameter(Test_obj.hvi.instructions.trigger_write.value,
                                   pyhvi.TriggerValue.ON)  # Specify trigger value that is going to be applyed

        instruction2 = sequence.programming.add_instruction('TriggerOff', 100,
                                                            Test_obj.hvi.instructions.trigger_write.id)  # Add trigger write instruction to the sequence
        instruction2.set_parameter(Test_obj.hvi.instructions.trigger_write.trigger,
                                   engine.triggers['PulseOut'])  # Specify which trigger is going to be used
        instruction2.set_parameter(Test_obj.hvi.instructions.trigger_write.sync_mode,
                                   pyhvi.SyncMode.IMMEDIATE)  # Specify synchronization mode
        instruction2.set_parameter(Test_obj.hvi.instructions.trigger_write.value,
                                   pyhvi.TriggerValue.OFF)  # Specify trigger value that is going to be applyed

    jump_name = 'JumpStatement'
    jump_time = 1000
    jump_destination = "Start"
    Test_obj.hvi.programming.add_jump(jump_name, jump_time, jump_destination)

    # Add global synchronized end to close KtHvi execution (close all sequences - using hvi-programming interface)
    Test_obj.hvi.programming.add_end('EndOfSequence', 10)

    # Assign triggers to KtHvi object to be used for HVI-managed synchronization, data sharing, etc
    Test_obj.hvi.platform.sync_resources = [pyhvi.TriggerResourceId.PXI_TRIGGER5, pyhvi.TriggerResourceId.PXI_TRIGGER6,
                                   pyhvi.TriggerResourceId.PXI_TRIGGER7]

    print("Configured HVI for mimo resync test")

def _fast_branching_hvi_configurator(Test_obj):

    moduleHviList = []
    for module in Test_obj.module_instances:
        if not module[0].hvi:
            print("Module in chassis {} and slot {} does not support HVI2.0... exiting".format(module.getChassis(), module.getSlot()))
            sys.exit()
        moduleHviList.append(module[0].hvi)

    ######################################
    ## Configure resources in HVI instance
    ######################################

    # Add engines to the engineList
    engineList = []
    for module in moduleHviList:
        engineList.append(module.engines.main_engine)

    # Create HVI instance
    moduleResourceName = "KtHvi"
    Test_obj.hvi = pyhvi.KtHvi(moduleResourceName)

    # Assign triggers to HVI object to be used for HVI-managed synch, data sharing, etc.
    triggerResources = [pyhvi.TriggerResourceId.PXI_TRIGGER0, pyhvi.TriggerResourceId.PXI_TRIGGER1,
                        pyhvi.TriggerResourceId.PXI_TRIGGER7]
    Test_obj.hvi.platform.sync_resources = triggerResources

    # Assign clock frequences that are outside the set of the clock frequencies of each hvi engine
    nonHVIclocks = [10e6]
    Test_obj.hvi.synchronization.non_hvi_core_clocks = nonHVIclocks

    if engineList.__len__() > 1:
        Test_obj.hvi.platform.chassis.add_auto_detect()

    # Get engine IDs
    engine_count = 0
    for engineID in engineList:
        Test_obj.hvi.engines.add(engineID, "SdEngine{}".format(engine_count))
        engine_count += 1

    ######################################
    ## Start HVI sequence creation
    ######################################

    print("Press enter to begin creation of the HVI sequence")
    input()

    # Create register cycleCnt in module0, the module waiting for external trigger events
    seq0 = Test_obj.hvi.engines[Test_obj.master_module_index].main_sequence
    cycleCnt = seq0.registers.add("cycleCnt", pyhvi.RegisterSize.SHORT)

    # Create a register WfNum in each PXI module. WfNum will be used to queue waveforms
    for index in range(0, Test_obj.hvi.engines.count):
        engine = Test_obj.hvi.engines[index]
        seq = engine.main_sequence
        seq.registers.add("WfNum", pyhvi.RegisterSize.SHORT)

    # Create list of module resources to use in HVI sequence
    waitTrigger = moduleHviList[Test_obj.master_module_index].triggers.pxi_2
    Test_obj.hvi.engines[Test_obj.master_module_index].events.add(waitTrigger, "extEvent")

    # Add wait statement to first engine sequence (using sequence.programming interface)
    waitEvent = seq0.programming.add_wait_event("wait_external_trigger", 10)
    waitEvent.event = Test_obj.hvi.engines[Test_obj.master_module_index].events["extEvent"]
    waitEvent.set_mode(pyhvi.EventDetectionMode.TRANSITION_TO_ACTIVE, pyhvi.SyncMode.IMMEDIATE)

    # Add wait trigger just to be sure Pxi from the cards is not interfering Pxi2 triggering from a third card (the trigger the waitEvent is waiting for).
    trigger = Test_obj.hvi.engines[Test_obj.master_module_index].triggers.add(waitTrigger, "extTrigger")
    trigger.configuration.direction = pyhvi.Direction.INPUT
    trigger.configuration.polarity = pyhvi.TriggerPolarity.ACTIVE_HIGH

    # Add global synchronized junction to HVI instance using hvi.programming interface
    junctionName = "GlobalJunction"
    junctionTime_ns = 10
    Test_obj.hvi.programming.add_junction(junctionName, junctionTime_ns)

    # Parameters for AWG queue WFM with register
    startDelay = 0
    nCycles = 1
    prescaler = 0
    nAWG = 1

    # Add actions to HVI engines
    for index in range(0, Test_obj.hvi.engines.count):
        moduleActions = Test_obj.module_instances[index][0].hvi.actions
        engine = Test_obj.hvi.engines[index]
        engine.actions.add(moduleActions.awg1_start, "awg_start1")
        # engine.actions.add(moduleActions.awg2_start, "awg_start2")
        # engine.actions.add(moduleActions.awg3_start, "awg_start3")
        # engine.actions.add(moduleActions.awg4_start, "awg_start4")

        engine.actions.add(moduleActions.awg1_trigger, "awg_trigger1")
        # engine.actions.add(moduleActions.awg2_trigger, "awg_trigger2")
        # engine.actions.add(moduleActions.awg3_trigger, "awg_trigger3")
        # engine.actions.add(moduleActions.awg4_trigger, "awg_trigger4")

    # Add AWG queue waveform and AWG trigger to each module's sequence
    for index in range(0, Test_obj.hvi.engines.count):
        engine = Test_obj.hvi.engines[index]

        # Obtain main sequence from engine to add instructions
        seq = engine.main_sequence

        # Add AWG queue waveform instruction to the sequence
        AwgQueueWfmInstrId = Test_obj.module_instances[index][0].hvi.instructions.queueWaveform.id
        AwgQueueWfmId = Test_obj.module_instances[index][0].hvi.instructions.queueWaveform.waveformNumber.id

        instruction0 = seq.programming.add_instruction("awgQueueWaveform", 10, AwgQueueWfmInstrId)
        instruction0.set_parameter(AwgQueueWfmId, seq.registers["WfNum"])
        instruction0.set_parameter(Test_obj.module_instances[index][0].hvi.instructions.queueWaveform.channel.id, nAWG)
        instruction0.set_parameter(Test_obj.module_instances[index][0].hvi.instructions.queueWaveform.triggerMode.id,
                                   keysightSD1.SD_TriggerModes.SWHVITRIG)
        instruction0.set_parameter(Test_obj.module_instances[index][0].hvi.instructions.queueWaveform.startDelay.id, startDelay)
        instruction0.set_parameter(Test_obj.module_instances[index][0].hvi.instructions.queueWaveform.cycles.id, nCycles)
        instruction0.set_parameter(Test_obj.module_instances[index][0].hvi.instructions.queueWaveform.prescaler.id, prescaler)


        awgTriggerList = [engine.actions["awg_trigger1"]]  #, engine.actions["awg_trigger2"], engine.actions["awg_trigger3"], engine.actions["awg_trigger4"]]
        instruction2 = seq.programming.add_instruction("AWG trigger", 2e3,
                                                       Test_obj.hvi.instructions.action_execute.id)
        instruction2.set_parameter(Test_obj.hvi.instructions.action_execute.action, awgTriggerList)

    # Increment cycleCnt in module0
    instructionRYinc = seq0.programming.add_instruction("add", 10, Test_obj.hvi.instructions.add.id)
    instructionRYinc.set_parameter(Test_obj.hvi.instructions.add.left_operand, 1)
    instructionRYinc.set_parameter(Test_obj.hvi.instructions.add.right_operand, cycleCnt)
    instructionRYinc.set_parameter(Test_obj.hvi.instructions.add.result_register, cycleCnt)

    # Global Jump
    jumpName = "jumpStatement"
    jumpTime = 10000
    jumpDestination = "Start"
    Test_obj.hvi.programming.add_jump(jumpName, jumpTime, jumpDestination)

    # Add global synchronized end to close HVI execution (close all sequences - using hvi-programming interface)
    Test_obj.hvi.programming.add_end("EndOfSequence", 100)

    Test_obj.seq_master = Test_obj.hvi.engines[Test_obj.master_module_index].main_sequence

    print("Configured HVI for fast branching test.")



