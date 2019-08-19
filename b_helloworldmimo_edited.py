import sys
import os
import pyhvi
sys.path.append('C:\Program Files (x86)\Keysight\SD1\Libraries\Python')
import keysightSD1
import argparse
from datetime import timedelta

"""HVI Hello World MIMO example

Keysight Confidential
Copyright Keysight Technologies 2019

Usage:  python helloworldmimo.py [--simulate]

HelloWorldMimo example compiles and runs two HVI sequences in two SD1 modules with each sequence 
turning ON and OFF a trigger.

First opens two SD1 cards (real hardware or simulation mode), creates two HVI modules from the cards,
adds a chassis (real hardware or simulated), gets the SD1 hvi engines and adds it to the HVI Instrument,
adds and configures the trigger used by each sequence, adds the instructions in both sequences,
compiles and runs.
         
      [module1]         [module2]
       Engine		      Engine    
       Seq 0             Seq 1			
     +-------+     	     +-------+	 
     | Start |	         | Start |	 
     +-------+     	     +-------+    
         | 10	           	 | 10      
   +----------+         +----------+	 
   |TriggerON |	        |TriggerON |	 
   +----------+	        +----------+	 
         |  10              |  10   
   +----------+     	+----------+	 
   |TriggerOFF|	        |TriggerOFF|	 
   +----------+	        +----------+	 
         |  10              |  10        
     +-------+	         +-------+	 
     |  End  |     	     |  End  |	 
     +-------+	         +-------+	
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
        options = 'simulate=true' if hardware_simulated else ''

        # Define list of module descriptors
        module_descriptors = [
            {'chassis_number': 1, 'slot_number': 9, 'options': options},
            {'chassis_number': 1, 'slot_number': 10, 'options': options}
        ]

        # Open SD modules
        module_list = []
        for descriptor in module_descriptors:
            module = keysightSD1.SD_AOU()
            id = module.openWithOptions('M3201A', descriptor['chassis_number'], descriptor['slot_number'], descriptor['options'])
            if id < 0:
                raise Exception(f"Error opening module in chassis: {descriptor['chassis_number']}, {descriptor['slot_number']}, opened with ID: {id}")
            module_list.append(module)

        # Obtain SD_AOUHvi interface from modules
        module_hvi_list = []
        for module in module_list:
            if not module.hvi:
                raise Exception(f'Module in chassis {module.chassis} and slot {module.slot} does not support HVI2')
            module_hvi_list.append(module.hvi)

        # Create list of triggers to use in KtHvi sequence
        trigger_list = [module_hvi_list[0].triggers.front_panel_1, module_hvi_list[1].triggers.front_panel_1]

        # Create KtHvi instance
        module_resource_name = 'KtHvi'
        hvi = pyhvi.KtHvi(module_resource_name)

	    # *********************************
	    # Config resource in KtHvi instance

        # Add chassis to KtHvi instance
        if hardware_simulated:
            hvi.platform.chassis.add_with_options(1, 'Simulate=True,DriverSetup=model=M9018B,NoDriver=True')
        else:
            hvi.platform.chassis.add_auto_detect()

        # Get engine IDs from module's SD_AOUHvi interface and add each engine to KtHvi instance
        engine_index = 0
        for module_hvi in module_hvi_list:
            sd_engine = module_hvi.engines.master_engine
            hvi.engines.add(sd_engine, f'SdEngine{engine_index}')
            engine_index += 1

        # Configure the trigger used by the sequence
        for index in range(0, hvi.engines.count):
            engine = hvi.engines[index]

            trigger = engine.triggers.add(trigger_list[index], 'SequenceTrigger')
            trigger.configuration.direction = pyhvi.Direction.OUTPUT
            trigger.configuration.drive_mode = pyhvi.DriveMode.PUSH_PULL
            trigger.configuration.trigger_polarity = pyhvi.TriggerPolarity.ACTIVE_LOW
            # trigger.configuration.trigger_polarity = pyhvi.TriggerPolarity.ACTIVE_HIGH
            trigger.configuration.delay = 0
            trigger.configuration.trigger_mode = pyhvi.TriggerMode.LEVEL
            trigger.configuration.pulse_length = 250

		# *******************************
		# Start KtHvi sequences creation

        for index in range(0, hvi.engines.count):
            # Get engine in the KtHvi instance
            engine = hvi.engines[index]

            # Obtain main sequence from engine to add instructions
            sequence = engine.main_sequence

            # Add instructions to specific sequence (using sequence.programming interface)
            instruction1 = sequence.programming.add_instruction('TriggerOn', 10, hvi.instructions.instructions_trigger_write.id)            # Add trigger write instruction to the sequence
            instruction1.set_parameter(hvi.instructions.instructions_trigger_write.trigger, engine.triggers['SequenceTrigger'])  # Specify which trigger is going to be used
            instruction1.set_parameter(hvi.instructions.instructions_trigger_write.sync_mode, pyhvi.SyncMode.IMMEDIATE)          # Specify synchronization mode
            instruction1.set_parameter(hvi.instructions.instructions_trigger_write.value, pyhvi.TriggerValue.ON)                 # Specify trigger value that is going to be applyed

            instruction2 = sequence.programming.add_instruction('TriggerOff', 500, hvi.instructions.instructions_trigger_write.id)          # Add trigger write instruction to the sequence
            instruction2.set_parameter(hvi.instructions.instructions_trigger_write.trigger, engine.triggers['SequenceTrigger'])  # Specify which trigger is going to be used
            instruction2.set_parameter(hvi.instructions.instructions_trigger_write.sync_mode, pyhvi.SyncMode.IMMEDIATE)          # Specify synchronization mode
            instruction2.set_parameter(hvi.instructions.instructions_trigger_write.value, pyhvi.TriggerValue.OFF)                # Specify trigger value that is going to be applyed

        # Add global synchronized end to close KtHvi execution (close all sequences - using hvi-programming interface)
        hvi.programming.add_end('EndOfSequence', 10)

        # Assign triggers to KtHvi object to be used for HVI-managed synchronization, data sharing, etc
        hvi.platform.sync_resources = [pyhvi.TriggerResourceId.PXI_TRIGGER0, pyhvi.TriggerResourceId.PXI_TRIGGER1]

        # Compile the instrument sequence(s)
        hvi.compile()       

        # Load the KtHvi instance to HW: load sequence(s), config triggers/events/..., lock resources, etc
        hvi.load_to_hw()    

         # Execute KtHvi instance
        time = timedelta(seconds=1)
        hvi.run(time)      
        
    except Exception as ex:
        print(ex)
        print('helloworldmimo.py encountered the error above - exiting')

    finally:
        # Release KtHvi instance from HW (unlock resources)
        if hvi:
            hvi.release_hw()

        # Close all modules
        for module in module_list:
            module.close()

if __name__ == '__main__':
    main()
