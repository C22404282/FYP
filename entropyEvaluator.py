



import time
import serial
from debugDriver import DebugPort
from ppk2_api.ppk2_api import PPK2_API
import subprocess
import numpy as np



PPK2_PORT = "COM12"
VOLTAGE = 3.3
UART_PORT = 'COM16'
BAUD_RATE = 115200


class entropyEvaluator:
    def __init__(self,targetBoard,ppk2_port,voltage,uart_port,baud_rate,buildFolder,entropyDatasetFolder,resultsFolder,NIST_PATH,BITS_PER_SAMPLE = 1):
        self.targetBoard = targetBoard
        self.PPK2_PORT = ppk2_port
        self.VOLTAGE = voltage
        self.UART_PORT = uart_port
        self.BAUD_RATE = baud_rate
        self.ENTROPYFOLDER = entropyDatasetFolder
        self.BUILD_FOLDER = buildFolder
        self.RESULT_FOLDER = resultsFolder
        self.dp = DebugPort()
        self.NIST_PATH = NIST_PATH
        self.BITS_PER_SAMPLE = BITS_PER_SAMPLE
        self.SEQ_OUTPUT_FILE_ORIG = self.ENTROPYFOLDER + "/" + self.targetBoard + "_seq_dataset_orig.bin"
        self.SEQ_OUTPUT_FILE_ORIG = self.SEQ_OUTPUT_FILE_ORIG.replace("\\", "/")
        self.RESTART_OUTPUT_FILE_ORIG = self.ENTROPYFOLDER + "/" + self.targetBoard + "_restart_matrix_orig.bin"
        self.RESTART_OUTPUT_FILE_ORIG = self.RESTART_OUTPUT_FILE_ORIG.replace("\\", "/")

        self.resultNum = 0
        if voltage > 5:
            print("Voltage set above 5V - defaulting to 3.3V")
            self.VOLTAGE = 3.3

        self.uart_init()
        self.ppk2_init(self.PPK2_PORT)


    def ppk2_init(self,PPK2_PORT):
        self.ppk2 = PPK2_API(PPK2_PORT) 
        self.clearPPK2_buffer()
        self.ppk2.get_modifiers() #Calibrates Device
        self.ppk2.use_source_meter()
        self.ppk2.set_source_voltage(int(self.VOLTAGE * 1000))

    
    def turnOnPico(self):
        self.ppk2.toggle_DUT_power("ON")
        time.sleep(0.05)

    def turnOffPico(self):
        self.ppk2.toggle_DUT_power("OFF")
        time.sleep(0.05)

    def clearPPK2_buffer(self):
        self.ppk2.stop_measuring()
        while True:
            self.ppk2.ser.reset_input_buffer()
            time.sleep(0.1)
            if self.ppk2.ser.in_waiting == 0:
                break
            self.ppk2.ser.read(self.ppk2.ser.in_waiting)

    def uart_init(self,timeout=5):
        self.uart = serial.Serial(self.UART_PORT, self.BAUD_RATE, timeout=timeout)

    def to_wsl_path(self, path_str):
        clean = path_str.replace("\\", "/")
        prefix = "//wsl.localhost/Ubuntu"
        if clean.startswith(prefix):
            return clean[len(prefix):]
        return clean

    def runSequentialTest(self):
        SAMPLE_COUNT = 1000000
        READ_BYTES = int(SAMPLE_COUNT/8)

        self.turnOnPico()

        elf_path = self.BUILD_FOLDER + "/entropy_sequential_test.elf"
        elf_path = elf_path.replace("\\", "/")

        print(elf_path)    

        self.dp.programBoard(elf_path)
        self.turnOffPico()
        self.uart.reset_input_buffer()
        self.uart.timeout = 20

        #self.uart.read(1) #To catch uart initialization
        failed = 0
        TEST_COMPLETE = False
        print("Starting Sequential Test")
        while not TEST_COMPLETE:
            try:
                if failed > 10:
                    raise RuntimeError("Sequential Entropy Test has failed more than 10 times\n")
                
                self.turnOnPico()
                raw_bytes = self.uart.read(READ_BYTES)
                        
                if len(raw_bytes) != READ_BYTES:
                    print(f"READING FAILED !!!\nGot {len(raw_bytes)} bytes\n----Restarting Pico----\n")
                    self.turnOffPico()
                    failed += 1
                    
                else:
                    TEST_COMPLETE = True
                    with open(self.SEQ_OUTPUT_FILE_ORIG, "wb") as f:
                        f.write(raw_bytes)
                    print("Successfull - Read ",READ_BYTES,"bytes")
                    self.turnOffPico()

            except KeyboardInterrupt:
                print("\n--EXITING--\n")
                break
            except RuntimeError:
                break
        return TEST_COMPLETE

    def runRestartTest(self):
        SAMPLE_SIZE_BITS = 1
        SAMPLES_PER_RESTART = 1000
        SAMPLES_PER_RESTART_BYTES = int(SAMPLES_PER_RESTART*SAMPLE_SIZE_BITS/8)

        elf_path = self.BUILD_FOLDER + "/entropy_restart_test.elf"
        elf_path = elf_path.replace("\\", "/")

        self.turnOnPico()
        self.dp.programBoard(elf_path)
        self.turnOffPico()


        open(self.RESTART_OUTPUT_FILE_ORIG, "wb").close() #Wipe all data first

        print("Starting Restart Test")
        TEST_COMPLETE = False
        while not TEST_COMPLETE:
            try:
                failed = 0
                successfull = 0
                for count in range(1,1001):
                    READING_SUCCESSFULL = False
                    while(not READING_SUCCESSFULL):
                        self.uart.reset_input_buffer()
                        self.turnOnPico()
                        raw_bytes = self.uart.read(SAMPLES_PER_RESTART_BYTES)
                        
                        if len(raw_bytes) != SAMPLES_PER_RESTART_BYTES:
                            print(f"READING {count} FAILED !!!\nGot {len(raw_bytes)} bytes\n----Restarting Pico----\n")
                            failed += 1
                            self.turnOffPico()
                            #time.sleep(0.05)
                        else:
                            READING_SUCCESSFULL = True
                            with open(self.RESTART_OUTPUT_FILE_ORIG, "ab") as f:
                                f.write(raw_bytes)

                            print(f"Sample {count} - succesfull")
                            successfull += 1
                            if successfull == 1000:
                                TEST_COMPLETE = True
                            self.turnOffPico()

            except KeyboardInterrupt:
                print("\n--EXITING--\n")
                break
        return TEST_COMPLETE
        


    def evaluate(self):
                
        try:
            
            #Start Sequential Test First            
            success = self.runSequentialTest()
            if (success):
                #Start Restart Test            
                success = self.runRestartTest()
                if(success):
                    results = self.runNIST()
                    minEntropy = min(results)
                    print("Min Entropy:",minEntropy)
                    return results
            else:
                raise RuntimeError("Sequential Test Failed")
                
        except KeyboardInterrupt:
            print("Error")
            return

    def expandBinaryFiles(self):
        
        seq_data = np.fromfile(self.SEQ_OUTPUT_FILE_ORIG, dtype=np.uint8)
        expanded_seq_data = np.unpackbits(seq_data)
        self.SEQ_OUTPUT_FILE_EXP = self.SEQ_OUTPUT_FILE_ORIG.replace("orig","exp")
        expanded_seq_data.tofile(self.SEQ_OUTPUT_FILE_EXP)


        restart_data = np.fromfile(self.RESTART_OUTPUT_FILE_ORIG, dtype=np.uint8)
        expanded_restart_data = np.unpackbits(restart_data)
        self.RESTART_OUTPUT_FILE_EXP = self.RESTART_OUTPUT_FILE_ORIG.replace("orig","exp")
        expanded_restart_data.tofile(self.RESTART_OUTPUT_FILE_EXP)


    def runNIST(self):
        print("Running NIST Tool")
        SEQ_TOOL_PATH = self.NIST_PATH + "/ea_non_iid"
        RESTART_TOOL_PATH = self.NIST_PATH + "/ea_restart"

        self.expandBinaryFiles()

        seq_tool = self.to_wsl_path(SEQ_TOOL_PATH)
        self.SEQ_OUTPUT_FILE_EXP = self.to_wsl_path(self.SEQ_OUTPUT_FILE_EXP)

        restart_tool = self.to_wsl_path(RESTART_TOOL_PATH)
        self.RESTART_OUTPUT_FILE_EXP = self.to_wsl_path(self.RESTART_OUTPUT_FILE_EXP)

        
        try:
            print("Calculating H_I")
            seq_result = subprocess.run(
                ["wsl",seq_tool, self.SEQ_OUTPUT_FILE_EXP, str(self.BITS_PER_SAMPLE)],
                capture_output=True,
                text=True,
                check=True
            )
            seqOutput = seq_result.stdout
            h_i = float(seqOutput[seqOutput.index(":") + 2:])

            print("Entropy_Original =",h_i)

        except subprocess.CalledProcessError as e:
            print("EXIT CODE:", e.returncode)
            print("STDOUT:\n", e.stdout)
            print("STDERR:\n", e.stderr)

        try:
            print("Calculating H_min")
            restart_result = subprocess.run(
                ["wsl", restart_tool, "-n", self.RESTART_OUTPUT_FILE_EXP, str(self.BITS_PER_SAMPLE),str(h_i)],
                capture_output=True,
                text=True,
                check=True
            )
            restartOutput = restart_result.stdout
            h_rI = restartOutput.index("H_r:")
            h_cI = restartOutput.index("H_c:")

            h_r = float(restartOutput[h_rI + 5:h_rI + 13])
            h_c = float(restartOutput[h_cI + 5:h_cI + 13])

            print("H_r =",h_r)
            print("H_c =",h_c)
            return [h_i,h_r,h_c]
        except subprocess.CalledProcessError as e:
            print("EXIT CODE:", e.returncode)
            print("STDOUT:\n", e.stdout)
            print("STDERR:\n", e.stderr)
        




build = r"\\wsl.localhost\Ubuntu\home\seanh\College\FYP\PicoW\build"
result = r"\\wsl.localhost\Ubuntu\home\seanh\College\FYP\PicoW\entropyResults"
entropyData = r"\\wsl.localhost\Ubuntu\home\seanh\College\FYP\PicoW\entropyDatasets"
nistPath = r"\\wsl.localhost\Ubuntu\home\seanh\College\FYP/SP800-90B_EntropyAssessment/cpp"
nistPath = nistPath.replace("\\","/")

eval = entropyEvaluator("PicoW","COM12",3.3,"COM16",115200,build,entropyData,result,nistPath)
# eval.SEQ_OUTPUT_FILE_ORIG = eval.ENTROPYFOLDER + "/" + eval.targetBoard + "_seq_dataset_orig.bin"
# eval.SEQ_OUTPUT_FILE_ORIG = eval.SEQ_OUTPUT_FILE_ORIG.replace("\\", "/")
# eval.RESTART_OUTPUT_FILE_ORIG = eval.ENTROPYFOLDER + "/" + eval.targetBoard + "_restart_matrix_orig.bin"
# eval.RESTART_OUTPUT_FILE_ORIG = eval.RESTART_OUTPUT_FILE_ORIG.replace("\\", "/")

eval.runNIST()








