import keysightSD1

awg8 = keysightSD1.SD_AOU()
awg8_id = awg8.openWithSlot("", 1, 9)

if awg8_id < 0:
    raise Exception

loop = True

while(loop):
    awg8.triggerIOconfig(keysightSD1.SD_TriggerDirections.AOU_TRG_OUT)
    awg8.triggerIOwrite(0, 1)
    awg8.triggerIOwrite(1, 1)
    awg8.triggerIOwrite(0, 1)
    print("press enter to loop")
    ipt = input()
    if ipt != "":
        loop = False