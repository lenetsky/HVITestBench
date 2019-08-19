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
    else:
        print("[ERROR] hardware_configurator.configure_hardware: Test object's test_key variable did not match a valid key")

# This is the hardware configurator for the helloworld test
def _helloworld_hw_config(Test_obj):
    print("No special AWG configuration needed for helloworld example.")

def _helloworldmimo_hw_config(Test_obj):
    print("No special AWG configuration needed for helloworldmimo example.")

def _mimo_resync_hw_config(Test_obj):
    print("To be done")