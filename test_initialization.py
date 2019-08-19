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

    def run_each_hvi(self):
        for hvi in range(0,len(self.hvi_instances)):
            hvi.compile()  # Compile the instrument sequence(s)
            hvi.load_to_hw()  # Load the instrument sequence(s) to HW
            time = timedelta(seconds=1)
            hvi.run(time)  # Execute the instrument sequence(s)

    def release_hvi(self):
        for hvi in range(0, len(self.hvi_instances)):
            hvi.release_hw()

class test_helloworldmimo(Test):
    # Dummy attributes
    # Add if needed

    # Attributes accessible through object initialization
    test_key = "helloworldmimo"

    # Attributes accessible through class methods
    number_modules = None
    hvi = None #This gets set in the hvi_configurator

    def __init__(self, module_dict):
        super().__init__(module_dict)
        self.number_modules = len(module_dict)

    def run_hvi(self):
        # Compile the instrument sequence(s)
        self.hvi.compile()

        # Load the KtHvi instance to HW: load sequence(s), config triggers/events/..., lock resources, etc
        self.hvi.load_to_hw()

         # Execute KtHvi instance
        time = timedelta(seconds=1)
        self.hvi.run(time)

    def release_hvi(self):
        self.hvi.release_hw()


class test_mimoresync(Test):
    # Dummy attributes
    # Add if needed

    # Attributes accessible through object initialization
    test_key = "mimoresync"

    # Attributes accessible through class methods
    number_modules = None # set in init()
    chassis_list = [] # set in init()
    hvi = None #This gets set in the hvi_configurator
    master_module_index = None #set in init()

    def __init__(self, module_dict, master_module_location): #master_module_location is a dict {chassis: x, slot: y}
        super().__init__(module_dict)
        self.number_modules = len(module_dict)
        for i in range(0, self.number_modules):
            self.chassis_list.append(self.module_instances[i][2][1])
            if master_module_location["chassis"] == self.module_instances[i][2][1] and master_module_location["slot"] == self.module_instances[i][2][1]:
                self.master_module_index = i

    def run_hvi(self):
        # Compile the instrument sequence(s)
        self.hvi.compile()

        # Load the KtHvi instance to HW: load sequence(s), config triggers/events/..., lock resources, etc
        self.hvi.load_to_hw()

         # Execute KtHvi instance
        time = timedelta(seconds=1)
        self.hvi.run(time)

    def release_hvi(self):
        self.hvi.release_hw()


class test_fastbranching(Test):
    # Dummy attributes
    # Add if needed

    # Attributes accessible through object initialization
    test_key = "fastbranching"

    # Attributes accessible through class methods
    number_modules = None # set in init()
    chassis_list = [] # set in init()
    hvi = None #This gets set in the hvi_configurator
    master_module_index = None #set in init()
    seq_master = None #set at end of hvi_configurator
    extTrigModule = keysightSD1.SD_AOU()

    def __init__(self, module_dict, master_module_location): #master_module_location is a dict {chassis: x, slot: y}
        super().__init__(module_dict)
        self.number_modules = len(module_dict)
        for i in range(0, self.number_modules):
            self.chassis_list.append(self.module_instances[i][2][1])
            if master_module_location["chassis"] == self.module_instances[i][2][1] and master_module_location["slot"] == self.module_instances[i][2][1]:
                self.master_module_index = i


    def run_hvi(self):
        # Compile the instrument sequence(s)
        self.hvi.compile()

        # Load the KtHvi instance to HW: load sequence(s), config triggers/events/..., lock resources, etc
        self.hvi.load_to_hw()

         # Execute KtHvi instance
        time = timedelta(seconds=1)
        self.hvi.run(time)

    def release_hvi(self):
        self.hvi.release_hw()

    def setup_ext_trig_module(self, chassis, slot):

        partNumber = ""

        # Connect to trigger module
        status = self.extTrigModule.openWithSlot(partNumber, chassis, slot)
        if (status < 0):
            print("Invalid module name, chassis, or slot number. Press enter to quit")
            input()
            sys.exit()

    def triggerPXI2(self, moduleAOU):
        moduleAOU.PXItriggerWrite(keysightSD1.SD_TriggerExternalSources.TRIGGER_PXI2, keysightSD1.SD_TriggerValue.HIGH)
        moduleAOU.PXItriggerWrite(keysightSD1.SD_TriggerExternalSources.TRIGGER_PXI2, keysightSD1.SD_TriggerValue.LOW)
        moduleAOU.PXItriggerWrite(keysightSD1.SD_TriggerExternalSources.TRIGGER_PXI2, keysightSD1.SD_TriggerValue.HIGH)

    def close_modules(self):
        for module_inst in self.module_instances:
            module_inst[0].close()

    def loop(self):
        wfNum = 1
        nWfm = 2

        # Loop as many times as desired, press q to exit
        while True:
            for index in range(0, self.hvi.engines.count):
                engine = self.hvi.engines[index]
                seq = engine.main_sequence
                seq.registers["WfNum"].write(wfNum)

            print(
                "N. of external triggers received at Module0: cycleCnt = {}".format(self.seq_master.registers["cycleCnt"].read()))
            print("Press enter to trigger PXI2, press q to exit")

            key = input()

            if key == 'q':
                break
            else:
                self.triggerPXI2(self.extTrigModule)

            # Change wfNum at each iteration
            if (wfNum >= nWfm):  # general case of nWfm
                wfNum = 1
            else:
                wfNum = wfNum + 1

            # Release HVI instance from HW (unlock resources)
        print("Exiting...")


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
