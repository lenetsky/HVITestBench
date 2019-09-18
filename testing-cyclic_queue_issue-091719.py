import keysightSD1
import time

num_waveforms = 1000
num_trigs = 1000

awg = keysightSD1.SD_AOU()
awg_id = awg.openWithSlot("", 1, 7)

# error_flush = awg.AWGflush(1)
error_waveshape = awg.channelWaveShape(1, keysightSD1.SD_Waveshapes.AOU_AWG)

wave = keysightSD1.SD_Wave()
error_createwave = wave.newFromFile(r"C:\Users\Administrator\PycharmProjects\HVITestBench\Sin_10MHz_20456_samples.csv")
# error_createwave = wave.newFromFile(r'C:\Users\Public\Documents\Keysight\SD1\Examples\Waveforms\Sin_10MHz_50samples_192cycles.csv')
error_waveformload = awg.waveformLoad(wave, 1, 0)

error_queueconfig = awg.AWGqueueConfig(1, keysightSD1.SD_QueueMode.CYCLIC)

for i in range(0,num_waveforms):
    error_queue = awg.AWGqueueWaveform(1, 1, keysightSD1.SD_TriggerModes.SWHVITRIG_CYCLE, 0, 1, 0)
    # awg.AWGqueueWaveform(nAWG, waveformNumber=, triggerMode=, startDelay=,cycles=,prescaler=)

for i in range(0,num_trigs):
    print("Sending %s trigger"%i)
    error_trigger = awg.AWGtrigger(1)
    time.sleep(.3)
