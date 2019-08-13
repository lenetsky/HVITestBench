import sys
sys.path.append('C:/Program Files (x86)/Keysight/SD1/Libraries/Python')
import keysightSD1
import pyhvi

# This is a switch that will route to the correct function to configure a given Test object's HVI sequence
def configure_hvi(Test_obj, filestr=""):
    if Test_obj.test_key == "HVI external trigger":
        _HVIexternaltrigger_hvi_config(Test_obj, filestr)
    elif Test_obj.test_key == "helloworld":
        _helloworld_hvi_configurator(Test_obj)
    else:
        print("[ERROR] hvi_configurator.configure_HVI: Test object's test_key variable did not match a valid key")

def _HVIexternaltrigger_hvi_config(Test_obj, filestr):
    Test_obj.set_hvi(filestr)

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
        sd_engine_aou = sd_hvi.engines.master_engine

        # Create KtHvi instance
        module_resource_name = 'KtHvi'
        hvi = pyhvi.KtHvi(module_resource_name)

        # Add SD HVI engine to KtHvi instance
        engine = hvi.engines.add(sd_engine_aou, 'SdEngine1')

        # Configure the trigger used by the sequence
        engine.triggers.add(sd_hvi.triggers.pxi_5, 'sequenceTrigger')
        trigger = engine.triggers['sequenceTrigger']
        trigger.configuration.direction = pyhvi.Direction.OUTPUT
        trigger.configuration.drive_mode = pyhvi.DriveMode.PUSH_PULL
        trigger.configuration.trigger_polarity = pyhvi.TriggerPolarity.ACTIVE_LOW
        trigger.configuration.delay = 0
        trigger.configuration.trigger_mode = pyhvi.TriggerMode.LEVEL
        trigger.configuration.pulse_length = 250

        # *******************************
        # Start KtHvi sequences creation
        # *******************************

        sequence = engine.main_sequence  # Obtain main squence from the created HVI instrument

        instruction1 = sequence.programming.add_instruction('TriggerOn', 10,
                                                            hvi.instructions.instructions_trigger_write.id)  # Add trigger write instruction to the sequence
        instruction1.set_parameter(hvi.instructions.instructions_trigger_write.trigger,
                                   sd_hvi.triggers.pxi_5)  # Specify which trigger is going to be used
        instruction1.set_parameter(hvi.instructions.instructions_trigger_write.sync_mode,
                                   pyhvi.SyncMode.IMMEDIATE)  # Specify synchronization mode
        instruction1.set_parameter(hvi.instructions.instructions_trigger_write.value,
                                   pyhvi.TriggerValue.ON)  # Specify trigger value that is going to be applied

        instruction2 = sequence.programming.add_instruction('TriggerOff', 100,
                                                            hvi.instructions.instructions_trigger_write.id)  # Add trigger write instruction to the sequence
        instruction2.set_parameter(hvi.instructions.instructions_trigger_write.trigger,
                                   sd_hvi.triggers.pxi_5)  # Specify which trigger is going to be used
        instruction2.set_parameter(hvi.instructions.instructions_trigger_write.sync_mode,
                                   pyhvi.SyncMode.IMMEDIATE)  # Specify synchronization mode
        instruction2.set_parameter(hvi.instructions.instructions_trigger_write.value,
                                   pyhvi.TriggerValue.OFF)  # Specify trigger value that is going to be applyed

        hvi.programming.add_end('EndOfSequence', 10)  # Add the end statement at the end of the sequence

        # Assign triggers to HVI object to be used for HVI-managed synchronization, data sharing, etc
        trigger_resources = [pyhvi.TriggerResourceId.PXI_TRIGGER5, pyhvi.TriggerResourceId.PXI_TRIGGER6]
        hvi.platform.sync_resources = trigger_resources

        Test_obj.hvi_instances.append(hvi)