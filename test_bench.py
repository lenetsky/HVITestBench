import sys
import time
sys.path.append('C:/Program Files (x86)/Keysight/SD1/Libraries/Python')
from hardware_configurator import *
from test_initialization import *
from hvi_configurator import *

module_1 = [1, 7]
module_2 = [1, 10]
master_module_location = [1, 7]
trigger_module_location = [1, 8]

# Create array of module locations [chassis, slot]. Doesn't matter what type of SD1 instrument (dig/awg)
module_array = [module_1, module_2]

# In this example we will run a trigger example that will use HVI to synchronize two modules in a single chassis

# This is the top level module which configures and runs sub-parts:
# triggerExample.py
#   1. test_initialization.py (Test initialization)
#   2. hardware_configurator.py (Hardware configuration)
#   3. hvi_configurator (HVI configuration)



# Use the inventory function to get more info about modules (instrument type, name, etc.)
module_dict = create_module_inventory(module_array)


# HelloWorld compiles and runs an HVI sequence consisting in a turning ON and OFF a trigger.
# First opens an SD1 card (real hardware or simulation mode), creates an HVI module from the card,
# gets the SD1 hvi engine and adds it to the HVI Instrument, adds and configures the trigger used by the sequence,
# adds the instructions, compiles and runs. It tests each module as part of a different HVI instrument. For example, if a
# chassis is filled with 17 modules, this test will NOT synchronize the trigger output of all modules. Rather, it will
# individually test the trigger of all 17 modules separately, one-by-one
#
#        Module
#         Eng1
#        Seq 0
#
#      +--------+
#      | Start  |
#      +--------+
#          | 10
#     +----------+
#     |TriggerON |
#     +----------+
#          |  10
#     +-----------+
#     |Trigger OFF|
#     +-----------+
#          |  10
#      +-------+
#      |  End  |
#      +-------+

print("Beginning test 1 of 4: a simple triggering test.")
print("Connect the trigger output of any/all module(s) to a digitizer or scope to observe pulse.")
print("Press any key to begin the test, or 'q' to quit.")
ctrl = input()
if ctrl == 'q':
    print("Exiting...")
    time.sleep(2)
    sys.exit

# set up test object
hello_world_test = test_helloworld(module_dict)

# run the hardware configurator
configure_hardware(hello_world_test)

# run the HVI configurator
configure_hvi(hello_world_test)

# run the HVIs
hello_world_test.run_each_hvi()

# release the HVIs
time.sleep(1)
hello_world_test.release_hvi()
hello_world_test.close_modules()
time.sleep(1)


# HVI Hello World MIMO
#
# HelloWorldMimo example compiles and runs two HVI sequences in two SD1 modules with each sequence
# turning ON and OFF a trigger.
#
# First opens the SD1 cards (real hardware or simulation mode), creates the HVI modules from the cards,
# adds a chassis (real hardware or simulated), gets the SD1 hvi engines and adds it to the HVI Instrument,
# adds and configures the trigger used by each sequence, adds the instructions in both sequences,
# compiles and runs.
#
#       [module1]         [module2]
#        Engine		      Engine
#        Seq 0             Seq 1
#      +-------+     	     +-------+
#      | Start |	         | Start |
#      +-------+     	     +-------+
#          | 10	           	     | 10
#    +----------+           +----------+
#    |TriggerON |	        |TriggerON |
#    +----------+	        +----------+
#          |  500                |  500
#    +----------+     	    +----------+
#    |TriggerOFF|	        |TriggerOFF|
#    +----------+	        +----------+
#          |  10                 |  10
#      +-------+	         +-------+
#      |  End  |     	     |  End  |
#      +-------+	         +-------+

print("Beginning test 2 of 4: a syncrhonized triggering test.")
print("Connect the trigger output of any/all module(s) to a digitizer or scope to observe synchronized pulses.")
print("Press any key to begin the test, or 'q' to quit.")
ctrl = input()
if ctrl == 'q':
    print("Exiting...")
    time.sleep(2)
    sys.exit

# create new test object
hello_world_mimo_test = test_helloworldmimo(module_dict)

# run the hardware configurator
configure_hardware(hello_world_mimo_test)

# run the HVI configurator
configure_hvi(hello_world_mimo_test)

# run
hello_world_mimo_test.run_hvi()

# release the HVI
time.sleep(1)
hello_world_mimo_test.release_hvi()
hello_world_mimo_test.close_modules()
time.sleep(1)


# MimoResync compiles and runs two HVI sequences in two SD1 modules.
#
# The first sequence has a wait for event statement that waits for a PXI2 signal to happen.
# Both sequences are then resynchronized with a junction statement and both execute a trigger ON
# and a trigger OFF instruction.
#
# First opens two SD1 cards (real hardware or simulation mode), creates two HVI modules from the cards,
# adds a chassis (real hardware or simulated), gets the SD1 hvi engines and adds it to the HVI Instrument,
# adds and configures the trigger used by each sequence, adds the instructions in both sequences,
# compiles and runs.
#
#   [moduleList[0]]     [moduleList[1]]
#        Engine             Engine
#        Seq 0              Seq 1
#      +-------+           +-------+
#      | Start |           | Start | /____
#      +-------+           +-------+ \    |
#          | 10               |           |
#    +------------+           |           |
#    |WaitForEvent|           |           |
#    +------------+           |           |
#          |  100             |  100      |
#    +----------+        +----------+     |
#    | Junction |        | Junction |     |
#    +----------+        +----------+     |
#          |  10              |  10       |
#    +----------+        +----------+     |
#    |TriggerON |        |TriggerON |     |
#    +----------+        +----------+     |
#          |  100             |  100      |
#    +----------+        +----------+     |
#    |TriggerOFF|        |TriggerOFF|     |
#    +----------+        +----------+     |
#          |  1000            |  1000     |
#    +----------+        +----------+     |
#    |   Jump   |        |   Jump   | ----+
#    +----------+        +----------+
#          |  10              |  10
#      +-------+           +-------+
#      |  End  |           |  End  |
#      +-------+           +-------+

print("Beginning test 3 of 4: a re-syncrhonized triggering test.")
print("Connect the trigger output of any/all module(s) to a digitizer or scope to observe synchronized pulses.")
print("Press any key to begin the test, or 'q' to quit.")

ctrl = input()
if ctrl == 'q':
    print("Exiting...")
    time.sleep(2)
    sys.exit

# create new test object
mimo_resync_test = test_mimoresync(module_dict, {"chassis": master_module_location[0], "slot": master_module_location[1]})

# run the hardware configurator
configure_hardware(mimo_resync_test)

# run the HVI configurator
configure_hvi(mimo_resync_test)

# run
mimo_resync_test.run_hvi()
print("press enter to continue")
input()
# release the HVI
time.sleep(1)
mimo_resync_test.release_hvi()
mimo_resync_test.close_modules()
time.sleep(1)



# Fast Branching test compiles and runs HVI sequences in two (or more) PXI modules. the first sequence has a wait for event statement that waits
# for a PXI2 signal to happen. Both sequences are then resynchronized with a junction statement and queue a waveform depending on a register value.
# Here the register WfNum is used to select the waveform to be queued. Another register, named cycleCnt in this example, is used as a counter
# to record the number of received external trigger events.

# This test first opens two SD1 cards (real hardware or simulation mode), creates two HVI modules from the cards, adds a chassis (real hardware or
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

print("Beginning test 4 of 4: a fast branching test.")
print("Connect the channel 1 output of any/all module(s) to a digitizer or scope to observe synchronized waveforms.")
print("Press any key to begin the test, or 'q' to quit.")

ctrl = input()
if ctrl == 'q':
    print("Exiting...")
    sys.exit

# create new test object
fast_branching_test = test_fastbranching(module_dict, {"chassis": master_module_location[0], "slot": master_module_location[1]})

# run the hardware configurator
configure_hardware(fast_branching_test)

# run the HVI configurator
configure_hvi(fast_branching_test)

# run
fast_branching_test.run_hvi()

# set up trigger module... replace the inputs with chassis, slot of your trigger module
fast_branching_test.setup_ext_trig_module(trigger_module_location)

# configure the test register
fast_branching_test.seq_master.registers["cycleCnt"].write(0)

# continuously loop through the test waveforms until user presses 'q'
fast_branching_test.loop()

# release the HVI
time.sleep(1)
fast_branching_test.release_hvi()
fast_branching_test.close_modules()
time.sleep(1)

"""
DONE!
"""

print("Test bench ran all tests. Press any key to quit")
print()
input()