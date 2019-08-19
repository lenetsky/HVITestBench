import sys
import os
import pyhvi
sys.path.append('C:\Program Files (x86)\Keysight\SD1\Libraries\Python')
import keysightSD1
import argparse
from datetime import timedelta

"""HVI Multi-Channel Sync Playback example
Example version for multi-chassis setup

Keysight Confidential
Copyright Keysight Technologies 2019

Usage:  python HD1_AN1_Multi.py [--simulate]

This example compiles and runs two HVI sequences in two SD1 modules. 

The first sequence has a wait for event statement that waits for a PXI2 signal trigger event to happen. 
Both sequences are then resynchronized with a junction statement and both execute an AWG trigger.

First opens two SD1 cards (real hardware or simulation mode), creates two HVI modules from the cards,
adds a chassis (real hardware or simulated), gets the SD1 hvi engines and adds it to the HVI Instrument,
adds and configures the trigger used by each sequence, adds the instructions in both sequences,
compiles and runs.
		 
  [moduleList[0]]	 [moduleList[1]]
	   Engine			 Engine	
	   Seq 0			  Seq 1		 
	 +-------+		   +-------+   
	 | Start |		   | Start | /____
	 +-------+		   +-------+ \	 |
		 | 10			   |		 |
   +------------+		   |		 |
   |WaitForEvent|		   |		 |
   +------------+		   |		 |
		 |  10			   |  10	 |
   +----------+		+----------+	 |
   | Junction |		| Junction |	 |
   +----------+		+----------+	 |
		 |  10			  |  10	     |
   +----------+		+----------+	 |
   |AWGtrigger|		|AWGtrigger|	 |
   +----------+		+----------+	 |
		 |  100			 |  100	     |
   +----------+		+----------+	 |
   |   Jump   |		|   Jump   | ----+ 
   +----------+		+----------+  
		 |  10			  |  10		
	 +-------+		  +-------+   
	 |  End  |		  |  End  |   
	 +-------+		  +-------+	 
"""

def awgQueueWaveform(moduleAOU):
	
	#AWG Channel Variables
	nChannels = 2
	hwVer = moduleAOU.getHardwareVersion()
	if hwVer < 4 :
		CHmin = 0
	else :
		CHmin= 1;
	
	#AWG Queue settings for all channels
	syncMode = keysightSD1.SD_SyncModes.SYNC_CLK10 #keysightSD1.SD_SyncModes.SYNC_CLK10 #keysightSD1.SD_SyncModes.SYNC_NONE
	queueMode = keysightSD1.SD_QueueMode.ONE_SHOT
	startDelay = 0
	prescaler = 0
	nCycles = 0
	#Trigger settings
	triggerMode = keysightSD1.SD_TriggerModes.SWHVITRIG_CYCLE
	
	#Load waveform to AWG memory
	moduleAOU.waveformFlush() #memory flush
	wave = keysightSD1.SD_Wave()
	wfmNum = 0
	wave.newFromFile("C:/Users/Public/Documents/Keysight/SD1/Examples/Waveforms/Gaussian.csv")
	moduleAOU.waveformLoad(wave, wfmNum)

	for nAWG in range(CHmin, CHmin+nChannels):
		#AWG queue flush 
		moduleAOU.AWGstop(nAWG)
		moduleAOU.AWGflush(nAWG)

		#Set AWG mode
		amplitude = 1
		moduleAOU.channelWaveShape(nAWG, keysightSD1.SD_Waveshapes.AOU_AWG)
		moduleAOU.channelAmplitude(nAWG, amplitude)
		
		#AWG configuration
		moduleAOU.AWGqueueConfig(nAWG, queueMode)
		moduleAOU.AWGqueueSyncMode(nAWG, syncMode)
		
		#Queue waveform to channel nAWG
		moduleAOU.AWGqueueWaveform(nAWG, wfmNum, triggerMode, startDelay, nCycles, prescaler)
		moduleAOU.AWGstart(nAWG) #AWG starts and wait for trigger
		moduleAOU.AWGtrigger(nAWG) #AWG trigger to output a first waveform before the HVI loop
	
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
			{'model_number': 'M3201A', 'chassis_number': 1, 'slot_number': 9, 'options': options },
			{'model_number': 'M3201A', 'chassis_number': 1, 'slot_number': 10, 'options': options }
		]

		# Open SD modules
		nModules = 0
		for descriptor in module_descriptors:
			module = keysightSD1.SD_AOU()
			id = module.openWithOptions(descriptor['model_number'], descriptor['chassis_number'], descriptor['slot_number'], descriptor['options'])
			if id < 0:
				raise Exception(f"Error opening module in chassis: {descriptor['chassis_number']}, {descriptor['slot_number']}, opened with ID: {id}")
			module_list.append(module)
			nModules +=1
		
		# Queue AWG Waveforms
		for index in range(0, nModules):
			awgQueueWaveform(module_list[index])

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
			hvi.platform.chassis.add_with_options(1, 'Simulate=True,DriverSetup=model=M9018B,NoDriver=True')
		else:
			hvi.platform.chassis.add_auto_detect()

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
		print("HVI Engine Count {} \n".format(hvi.engines.count))
		
		# *******************************
		# Start KtHvi sequences creation

		# Add wait statement to first engine sequence (using sequence.programming interface)
		engine_aou1_sequence = hvi.engines[0].main_sequence
		wait_event = engine_aou1_sequence.programming.add_wait_event('wait external_trigger', 10)
		wait_event.event = hvi.engines[0].events['StartEvent']
		wait_event.set_mode(pyhvi.EventDetectionMode.HIGH, pyhvi.SyncMode.IMMEDIATE)   # Configure event detection and synchronization modes

		# Add global synchronized junction to HVI instance (to all sequences!!! - using hvi.programming interface)
		global_junction = 'GlobalJunction'
		junction_time_ns = 10
		hvi.programming.add_junction(global_junction, junction_time_ns)
		
		#Create a list of possible actions for AWG modules 
		actions = module_list[0].hvi.actions
		# Define global AWG Trigger Action and Add it to the HVI Engine
		hvi.engines[0].actions.add(actions.awg1_trigger, 'AWG1_trigger')
		hvi.engines[0].actions.add(actions.awg2_trigger, 'AWG2_trigger')
		hvi.engines[0].actions.add(actions.awg3_trigger, 'AWG3_trigger')
		hvi.engines[0].actions.add(actions.awg4_trigger, 'AWG4_trigger')

		#Add AWG trigger to each module's sequence
		for index in range(0, hvi.engines.count):
			# Get engine in the KtHvi instance
			engine = hvi.engines[index]
			
			# Obtain main sequence from engine to add instructions
			sequence = engine.main_sequence
			
			#list of module possible actions
			actionList = [hvi.engines[0].actions['AWG1_trigger'], hvi.engines[0].actions['AWG2_trigger'], hvi.engines[0].actions['AWG3_trigger'], hvi.engines[0].actions['AWG4_trigger']]
			
			#Add AWG trigger instruction to the sequence
			actionExecute = hvi.instructions.instructions_action_execute
			instruction1 = sequence.programming.add_instruction("AWG trigger", 100, actionExecute.id)
			instruction1.set_parameter(actionExecute.action, actionList)
		
		#Synchronized jump
		jump_name = 'JumpStatement'
		jump_time = 1000
		jump_destination = "Start"
		hvi.programming.add_jump(jump_name, jump_time, jump_destination)

		# Add global synchronized end to close KtHvi execution (close all sequences - using hvi-programming interface)
		hvi.programming.add_end('EndOfSequence', 10)

		# Assign triggers to KtHvi object to be used for HVI-managed synchronization, data sharing, etc
		#NOTE: In a multi-chassis setup ALL the PXI lines listed below need to be shared among each squid board pair by means of SMB cable connections
		hvi.platform.sync_resources = [pyhvi.TriggerResourceId.PXI_TRIGGER5, pyhvi.TriggerResourceId.PXI_TRIGGER6, pyhvi.TriggerResourceId.PXI_TRIGGER7]
		
		#Assign clock frequencies that are outside the set of the clock frequencies of each HVI engine
		hvi.synchronization.non_hvi_core_clocks = [10e6]
		
		#Force synchronization
		hvi.synchronization.synchronize(True)
		
		# Compile the instrument sequence(s)
		hvi.compile()
		print("HVI Compiled")
		
		# Load the KtHvi instance to HW: load sequence(s), config triggers/events/..., lock resources, etc
		hvi.load_to_hw()	
		print("HVI Loaded to HW")

		 # Execute KtHvi instance
		time = timedelta(seconds=0)
		hvi.run(time)
		print("HVI Running...")

		# If running with hardware, stop execution here until the user presses a key to finish
		if not hardware_simulated:
			print("Press enter to finish...")
			input()

	except Exception as ex:
		print(ex)
		print('HD1_AN1_Multi.py encountered the error above - exiting')

	finally:
		# Release KtHvi instance from HW (unlock resources)
		if hvi:
			hvi.release_hw()

		# Close all modules
		for module in module_list:
			module.close()

if __name__ == '__main__':
	main()
