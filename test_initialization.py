import sys
sys.path.append('C:/Program Files (x86)/Keysight/SD1/Libraries/Python')
from abc import ABC, abstractmethod
import keysightSD1
from datetime import timedelta
import numpy

# Test initialization and configuration.

class Test(ABC):

    # Test class contains base properties and methods that will be present in all sub-classes

    module_dict = {} #dictionary of modules that we will be using the test, with chassis and slot information

    #===================== CORE OBJECT THAT TESTS ACT ON ====================#
    module_instances = [] # FORMAT: [INSTANCE, MODULE NAME, [CHASSIS SLOT]]
    #========================================================================#

    # init method will fill _module_instances list with SD objects specified by locations in module_dict
    @abstractmethod
    def __init__(self, module_dict):
        super().__init__()
        self.module_dict = module_dict
        for key, value in self.module_dict.items():
            if key[2] == '1':
                sd1_obj = keysightSD1.SD_AIN()
                sd1_obj_id = sd1_obj.openWithSlot("", value[0], value[1])
                if sd1_obj_id < 0:
                    print("[ERROR] Test.__init__: Error opening {}".format(key))
                self.module_instances.append([sd1_obj, key, value])
            elif key[2] == '2':
                sd1_obj = keysightSD1.SD_AOU()
                sd1_obj_id = sd1_obj.openWithSlot("", value[0], value[1])
                if sd1_obj_id < 0:
                    print("[ERROR] Test.__init__: Error opening {}".format(key))
                self.module_instances.append([sd1_obj, key, value])
            else:
                print("[ERROR] Test.__init__: Did not properly parse instrument type string.")

    # @abstractmethod
    # def _associate(self):
    #     pass


# class Test_HVIexternaltrigger(Test):
#
#     # Dummy attributes
#     Amplitude = 1
#     wave_id = 1
#     prescaler = 0
#     start_delay = 0
#     cycles = 0
#
#     # Attributes accessible through object initialization
#     test_key = "HVI external trigger"
#     module_a_slot = None
#     module_a_channel = None
#     module_b_slot = None
#     module_b_channel = None
#
#     # Attributes accessible through class methods
#     module_a = keysightSD1.SD_AOU()
#     module_b = keysightSD1.SD_AOU()
#     waveform = keysightSD1.SD_Wave()
#     hvi = keysightSD1.SD_HVI()
#
#     def __init__(self, module_dict, module_a_slot, module_a_channel,module_b_slot, module_b_channel):
#         super().__init__(module_dict)
#         self.module_a_slot = module_a_slot
#         self.module_a_channel = module_a_channel
#         self.module_b_slot = module_b_slot
#         self.module_b_channel = module_b_channel
#         self._associate()
#
#  # This private method associates the module modules (publicly accessible) of this test with the modules
#     # created in the base class
#     def _associate(self):
#         for module in self._module_instances:
#             if module[2][1] == self.module_a_slot:  # if a module was found in master_slot, assign it to master_module
#                 self.module_a = module[0]
#             elif module[2][1] == self.module_b_slot:
#                 self.module_b = module[0]
#             else:
#                 print("[ERROR] Associate function: Module found in slot that was not specified as master or slave")
#
#     def send_PXI_trigger_pulse(self, PXI_line_nbr, delay=.2):
#         time.sleep(delay)
#         self.module.PXItriggerWrite(PXI_line_nbr, 0)
#         time.sleep(delay)
#         self.module.PXItriggerWrite(PXI_line_nbr, 1)
#
#     def set_waveform(self, filestr):
#         self.waveform.newFromFile(filestr)
#         print("Loaded {} into HVI Trigger Sync Test's waveform".format(filestr))
#
#     def set_hvi(self, filestr):
#         self.hvi.open(filestr)
#         self.hvi.compile()
#         self.hvi.load()
#         print("Loaded {}.HVI into HVI Trigger Sync Test".format(filestr))



class test_helloworld(Test):
    # Dummy attributes
    # Add if needed

    # Attributes accessible through object initialization
    test_key = "helloworld"

    # Attributes accessible through class methods
    number_modules = None
    hvi_instances = []


    def __init__(self, module_dict):
        super().__init__(module_dict)
        self.number_modules = len(module_dict)

    def run_all_hvi(self):
        for hvi in range(0,len(self.hvi_instances)):
            hvi.compile()  # Compile the instrument sequence(s)
            hvi.load_to_hw()  # Load the instrument sequence(s) to HW
            time = timedelta(seconds=1)
            hvi.run(time)  # Execute the instrument sequence(s)




def create_module_inventory(module_array):
    # Takes array of module locations in format [chassis, slot], and returns a dictionary of modules with specific module type & location information

    dictionary = {}

    for mod in module_array:
        temp_mod = keysightSD1.SD_AOU() #Doesn't matter if it's dig or awg, it will be able to retrieve module name
        module_type = temp_mod.getProductNameBySlot(mod[0], mod[1])

        print("Found {} in Chassis {}, Slot {}".format(module_type, mod[0], mod[1]))

        name = "{}_chassis{}_slot{}".format(module_type, mod[0], mod[1])
        dictionary.update({name: [mod[0], mod[1]]})
        temp_mod.close()

    return dictionary