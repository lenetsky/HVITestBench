import sys

sys.path.append('C:\Program Files (x86)\Keysight\SD1\Libraries\Python')
import keysightSD1 as KSAPI

if __name__ == '__main__':

    CHANNEL = 1
    SLOT = 2

    # pulse count = 10 will cause the awg to continually play waveforms without triggers being applied
    PULSE_COUNT = 5

    sl = KSAPI.SD_AOU()
    sl.openWithSlot('', 1, SLOT)
    sl.AWGqueueConfig(CHANNEL, KSAPI.SD_QueueMode.CYCLIC)
    sl.channelAmplitude(CHANNEL, 1)
    sl.channelWaveShape(CHANNEL, KSAPI.SD_Waveshapes.AOU_AWG)
    sl.triggerIOconfig(KSAPI.SD_TriggerDirections.AOU_TRG_IN)
    sl.AWGfreezeOnStopEnable(CHANNEL, True)
    sl.channelOffset(CHANNEL, 0)
    sl.AWGflush(CHANNEL)

    high = [1] * 500
    low = [0] * 500
    data = low + (high * 2) + low
    data = data * PULSE_COUNT

    wv = KSAPI.SD_Wave()
    err = wv.newFromArrayDouble(0, data)
    err = sl.waveformLoad(wv, 0)
    for _ in range(1000):
        err = sl.AWGqueueWaveform(CHANNEL, 0, KSAPI.SD_TriggerModes.EXTTRIG, 0, 1, 2)
    sl.AWGstart(CHANNEL)
