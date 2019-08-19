import sys
sys.path.append('C:/Program Files (x86)/Keysight/SD1/Libraries/Python')
import keysightSD1

# This is a switch that will route the top-level script to the correct function to configure the test's hardware
def configure_hardware(Test_obj):
    if Test_obj.test_key == "helloworld":
        _helloworld_hw_config(Test_obj)
    elif Test_obj.test_key == "helloworldmimo":
        _helloworldmimo_hw_config(Test_obj)
    elif Test_obj.test_key == "mimoresync":
        _mimo_resync_hw_config(Test_obj)
    elif Test_obj.test_key == "fastbranching":
        _fast_branching_hw_config()
    else:
        print("[ERROR] hardware_configurator.configure_hardware: Test object's test_key variable did not match a valid key")

# This is the hardware configurator for the helloworld test
def _helloworld_hw_config(Test_obj):
    print("No special AWG configuration needed for helloworld test.")

def _helloworldmimo_hw_config(Test_obj):
    print("No special AWG configuration needed for helloworldmimo test.")

def _mimo_resync_hw_config(Test_obj):
    print("No special AWG configuration need for mimo resync test.")

def _fast_branching_hw_config(Test_obj):

    # Need to configure each module in the test
    for module_inst in Test_obj.module_instances:
        moduleAOU = module_inst[0]

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
        error = moduleAOU.waveformLoad(wave1, wfmNum1)
        if (error < 0):
            print("WaveformLoad1 error ", error)

        moduleAOU.AWGstart(nAWG)

