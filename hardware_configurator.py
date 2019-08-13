import sys
sys.path.append('C:/Program Files (x86)/Keysight/SD1/Libraries/Python')
import keysightSD1

# This is a switch that will route the top-level script to the correct function to configure the test's hardware
def configure_hardware(Test_obj):
    if Test_obj.test_key == "HVI external trigger":
        _HVIexternaltrigger(Test_obj)
    elif Test_obj.test_key == "helloworld":
        _helloworld_hw_config(Test_obj)
    else:
        print("[ERROR] hardware_configurator.configure_hardware: Test object's test_key variable did not match a valid key")

def _HVIexternaltrigger(Test_obj):

    awg_a = Test_obj.module_a
    awg_b = Test_obj.module_b

    awg_a.channelWaveShape(Test_obj.module_a_channel, keysightSD1.SD_Waveshapes.AOU_AWG)
    awg_b.channelWaveShape(Test_obj.module_b_channel, keysightSD1.SD_Waveshapes.AOU_AWG)
    awg_a.waveformFlush()
    awg_a.AWGflush(Test_obj.module_a_channel)
    awg_b.waveformFlush()
    awg_b.AWGflush(Test_obj.module_b_channel)

    awg_a.waveformLoad(Test_obj.waveform, Test_obj.wave_id)
    awg_b.waveformLoad(Test_obj.waveform, Test_obj.wave_id)

    awg_a.AWGqueueWaveform(Test_obj.module_a_channel,
                           Test_obj.wave_id,
                           keysightSD1.SD_TriggerModes.SWHVITRIG,
                           Test_obj.start_delay,
                           Test_obj.cycles,
                           Test_obj.prescaler)
    awg_b.AWGqueueWaveform(Test_obj.module_b_channel,
                           Test_obj.wave_id,
                           keysightSD1.SD_TriggerModes.SWHVITRIG,
                           Test_obj.start_delay,
                           Test_obj.cycles,
                           Test_obj.prescaler)
    awg_a.AWGqueueConfig(Test_obj.module_a_channel, keysightSD1.SD_QueueMode.CYCLIC)
    awg_b.AWGqueueConfig(Test_obj.module_b_channel, keysightSD1.SD_QueueMode.CYCLIC)
    awg_a.AWGstart(Test_obj.module_a_channel)
    awg_b.AWGstart(Test_obj.module_b_channel)

# This is the hardware configurator for the helloworld test
def _helloworld_hw_config(Test_obj):
    print("No hardware configuration needed for helloworld example.")