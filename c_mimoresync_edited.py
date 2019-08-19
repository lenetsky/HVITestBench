import sys
import os
import pyhvi
sys.path.append('C:\Program Files (x86)\Keysight\SD1\Libraries\Python')
import keysightSD1
import argparse
from datetime import timedelta

"""HVI MIMO Resync example

Keysight Confidential
Copyright Keysight Technologies 2019

Usage:  python mimoresync.py [--simulate]

MimoResync example compiles and runs two HVI sequences in two SD1 modules. 

The first sequence has a wait for event statement that waits for a PXI2 signal to happen. 
Both sequences are then resynchronized with a junction statement and both execute a trigger ON
and a trigger OFF instruction. 

First opens two SD1 cards (real hardware or simulation mode), creates two HVI modules from the cards,
adds a chassis (real hardware or simulated), gets the SD1 hvi engines and adds it to the HVI Instrument,
adds and configures the trigger used by each sequence, adds the instructions in both sequences,
compiles and runs.
         
  [moduleList[0]]     [moduleList[1]]
       Engine             Engine    
       Seq 0              Seq 1         
     +-------+           +-------+   
     | Start |           | Start | /____
     +-------+           +-------+ \    |
         | 10               |           |
   +------------+           |           |
   |WaitForEvent|           |           |
   +------------+           |           |
         |  10              |  10       |
   +----------+        +----------+     |
   | Junction |        | Junction |     |
   +----------+        +----------+     |
         |  10              |  10       |
   +----------+        +----------+     |
   |TriggerON |        |TriggerON |     |
   +----------+        +----------+     |
         |  100             |  100      |
   +----------+        +----------+     |
   |TriggerOFF|        |TriggerOFF|     |
   +----------+        +----------+     |
         |  1000            |  1000     |
   +----------+        +----------+     |
   |   Jump   |        |   Jump   | ----+ 
   +----------+        +----------+  
         |  10              |  10        
     +-------+           +-------+   
     |  End  |           |  End  |   
     +-------+           +-------+     
"""

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--simulate', help='Enable hardware simulation', action='store_true')
    return parser.parse_args()

def main():
    # Initialize variables used in 'finally:' block (in case an exception is thrown early)
    hvi = 0
    module_list = []

    try:
        # Parse the optional --simulate argument
        args = parse_args()
        hardware_simulated = args.simulate

        # Set the options string based on the value of the optional --simulate argument
        options = 'HVI2=true,factory=true,' + ('simulate=true' if hardware_simulated else '')

        # Define list of module descriptors
        module_descriptors = [
            {'model_number': 'M3201A', 'chassis_number': 1, 'slot_number': 9, 'options': options },
            {'model_number': 'M3201A', 'chassis_number': 1, 'slot_number': 10, 'options': options }
            # {'model_number': 'M3201A', 'chassis_number': 1, 'slot_number': 3, 'options': options },
            # {'model_number': 'M3201A', 'chassis_number': 1, 'slot_number': 8, 'options': options },
            # {'model_number': 'M3201A', 'chassis_number': 2, 'slot_number': 17, 'options': options },
            # {'model_number': 'M3201A', 'chassis_number': 3, 'slot_number': 15, 'options': options },
            # {'model_number': 'M3201A', 'chassis_number': 4, 'slot_number': 16, 'options': options }
        ]

        chassis_list = set()

        # Open SD modules
        for descriptor in module_descriptors:
            module = keysightSD1.SD_AOU()
            id = module.openWithOptions(descriptor['model_number'], descriptor['chassis_number'], descriptor['slot_number'], descriptor['options'])
            if id < 0:
                raise Exception(f"Error opening module in chassis: {descriptor['chassis_number']}, {descriptor['slot_number']}, opened with ID: {id}")
            module_list.append(module)
            chassis_list.add(descriptor['chassis_number'])

        # Obtain SD_AOUHvi interface from modules
        module_hvi_list = []
        for module in module_list:
            if not module.hvi:
                raise Exception(f'Module in chassis {module.chassis} and slot {module.slot} does not support HVI2')
            module_hvi_list.append(module.hvi)

        # Create lists of triggers to use in KtHvi sequence
        wait_trigger = module_hvi_list[0].triggers.pxi_2
        trigger_list = []
        engine_list = []
        for module in module_hvi_list:
            trigger_list.append(module.triggers.front_panel_1)
            engine_list.append(module.engines.master_engine)

        # Create KtHvi instance
        module_resource_name = 'KtHvi'
        hvi = pyhvi.KtHvi(module_resource_name)

        # *********************************
        # Config resource in KtHvi instance

        # Add chassis to KtHvi instance
        if hardware_simulated:
            for chassis_number in chassis_list:
                hvi.platform.chassis.add_with_options(chassis_number, 'Simulate=True,DriverSetup=model=M9018B,NoDriver=True')
        else:
            hvi.platform.chassis.add_auto_detect()

        # interconnects = hvi.platform.interconnects
        # interconnects.add_squidboards(1, 9, 2, 9)
        # interconnects.add_squidboards(2, 14, 3, 9)
        # interconnects.add_squidboards(3, 14, 4, 9)

        # Add each engine to KtHvi instance
        engine_index = 0
        for engine in engine_list:
            hvi.engines.add(engine, f'SdEngine{engine_index}')
            engine_index += 1

        # Add wait trigger just to be sure Pxi from the cards is not interfering Pxi2 triggering from a third card (the trigger the waitEvent is waiting for).
        start_trigger = hvi.engines[0].triggers.add(wait_trigger, 'StartTrigger')
        start_trigger.configuration.direction = pyhvi.Direction.INPUT
        start_trigger.configuration.trigger_polarity = pyhvi.TriggerPolarity.ACTIVE_LOW

        # Add start event
        start_event = hvi.engines[0].events.add(wait_trigger, 'StartEvent')

        for index in range(0, hvi.engines.count):
            # Get engine in the KtHvi instance
            engine = hvi.engines[index]

            # Add trigger to engine
            trigger = engine.triggers.add(trigger_list[index], 'PulseOut')
            trigger.configuration.direction = pyhvi.Direction.OUTPUT
            trigger.configuration.drive_mode = pyhvi.DriveMode.PUSH_PULL
            trigger.configuration.trigger_polarity = pyhvi.TriggerPolarity.ACTIVE_LOW
            trigger.configuration.delay = 0
            trigger.configuration.trigger_mode = pyhvi.TriggerMode.LEVEL
            trigger.configuration.pulse_length = 250

        # *******************************
        # Start KtHvi sequences creation

        # Add wait statement to first engine sequence (using sequence.programming interface)
        engine_aou1_sequence = hvi.engines[0].main_sequence
        wait_event = engine_aou1_sequence.programming.add_wait_event('wait external_trigger', 10)
        wait_event.event = hvi.engines[0].events['StartEvent']
        wait_event.set_mode(pyhvi.EventDetectionMode.HIGH, pyhvi.SyncMode.IMMEDIATE)   # Configure event detection and synchronization modes

        # Add global synchronized junction to HVI instance (to all sequences!!! - using hvi.programming interface)
        global_junction = 'GlobalJunction'
        junction_time_ns = 100
        hvi.programming.add_junction(global_junction, junction_time_ns)

        for index in range(0, hvi.engines.count):
            # Get engine in the KtHvi instance
            engine = hvi.engines[index]

            # Obtain main sequence from engine to add instructions
            sequence = engine.main_sequence

            # Add instructions to specific sequence (using sequence.programming interface)
            instruction1 = sequence.programming.add_instruction('TriggerOn', 10, hvi.instructions.instructions_trigger_write.id)    # Add trigger write instruction to the sequence
            instruction1.set_parameter(hvi.instructions.instructions_trigger_write.trigger, engine.triggers['PulseOut']) # Specify which trigger is going to be used
            instruction1.set_parameter(hvi.instructions.instructions_trigger_write.sync_mode, pyhvi.SyncMode.IMMEDIATE)  # Specify synchronization mode
            instruction1.set_parameter(hvi.instructions.instructions_trigger_write.value, pyhvi.TriggerValue.ON)         # Specify trigger value that is going to be applyed

            instruction2 = sequence.programming.add_instruction('TriggerOff', 100, hvi.instructions.instructions_trigger_write.id)  # Add trigger write instruction to the sequence
            instruction2.set_parameter(hvi.instructions.instructions_trigger_write.trigger, engine.triggers['PulseOut']) # Specify which trigger is going to be used
            instruction2.set_parameter(hvi.instructions.instructions_trigger_write.sync_mode, pyhvi.SyncMode.IMMEDIATE)  # Specify synchronization mode
            instruction2.set_parameter(hvi.instructions.instructions_trigger_write.value, pyhvi.TriggerValue.OFF)        # Specify trigger value that is going to be applyed

        jump_name = 'JumpStatement'
        jump_time = 1000
        jump_destination = "Start"
        hvi.programming.add_jump(jump_name, jump_time, jump_destination)

        # Add global synchronized end to close KtHvi execution (close all sequences - using hvi-programming interface)
        hvi.programming.add_end('EndOfSequence', 10)

        # Assign triggers to KtHvi object to be used for HVI-managed synchronization, data sharing, etc
        hvi.platform.sync_resources = [pyhvi.TriggerResourceId.PXI_TRIGGER5, pyhvi.TriggerResourceId.PXI_TRIGGER6, pyhvi.TriggerResourceId.PXI_TRIGGER7]

        # Compile the instrument sequence(s)
        hvi.compile()

        # Load the KtHvi instance to HW: load sequence(s), config triggers/events/..., lock resources, etc
        hvi.load_to_hw()

        # Execute KtHvi instance
        time = timedelta(seconds=0)
        hvi.run(time)

        # If running with hardware, stop execution here until the user presses a key to finish
        if not hardware_simulated:
            print("Press enter to finish...")
            input()

    except Exception as ex:
        print(ex)
        print('mimoresync.py encountered the error above - exiting')

    finally:
        # Release KtHvi instance from HW (unlock resources)
        if hvi:
            hvi.release_hw()

        # Close all modules
        for module in module_list:
            module.close()

if __name__ == '__main__':
    main()
