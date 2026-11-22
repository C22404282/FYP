
import time
import serial
from debugDriver import DebugPort
from ppk2_api.ppk2_api import PPK2_API
import json
import threading
import subprocess




class mlkemEvaluator:
    def __init__(self,targetBoard,ppk2_port,voltage,uart_port,baud_rate,buildFolder,resultsFolder):
        self.targetBoard = targetBoard
        self.PPK2_PORT = ppk2_port
        self.VOLTAGE = voltage
        self.UART_PORT = uart_port
        self.BAUD_RATE = baud_rate
        self.BUILD_FOLDER = buildFolder
        self.dp = DebugPort()
        
        self.resultsFolder = resultsFolder
        self.resultNum = 0
        if voltage > 5:
            print("Voltage set above 5V - defaulting to 3.3V")
            self.VOLTAGE = 3.3

        # self.uart_init()
        # self.ppk2_init(self.PPK2_PORT)

    # def configureGPIO(self,config):
    #     '''
    #     {
    #         0:{
    #            'operation': "KeyPair Gen",
    #            'gpio': 15
    #         },
    #         1:{
    #             'operation': "Encapsulation",
    #             'gpio': 14
    #         }               
    #     }
    #     '''

    #     self.gpioConfig = config

    def printResults(self,results):
        ops = ['KeyPair Generation','Encapsulation','Decapsulation']
        print(f"Algorithm:{results['algorithm']}")
        print(f"Iterations:{results['iterations']}")
        for key in results:
            for op in ops:
                if key in op.lower():
                    print(f"{op}:")
                    print(f" --Average Cycles: {round(results[key]['avg_cycles'])}")
                    print(f" --Peak Stack Usage: {results[key]['stackUsage']}")
        print("\n")



    def ppk2_init(self,PPK2_PORT):
        self.ppk2 = PPK2_API(PPK2_PORT) 
        self.clearPPK2_buffer()
        self.ppk2.get_modifiers() #Calibrates Device
        self.ppk2.use_source_meter()
        self.ppk2.set_source_voltage(int(self.VOLTAGE * 1000))
    
    # def ppk2_logger(self):
    #     ppk2 = self.ppk2
    #     ppk2.start_measuring()
    #     while not self.stop_sampling.is_set():
    #         raw = ppk2.get_data()
    #         if raw != b"": #If data
    #             samples, digital = ppk2.get_samples(raw)
    #             self.all_samples.extend(samples)
    #             self.all_digital.extend(digital)
    #         time.sleep(0.005)  #Let buffer fill

    #     #Get extra data left in buffer
    #     raw = ppk2.get_data()
    #     if raw != b"":
    #         samples, digital = ppk2.get_samples(raw)
    #         self.all_samples.extend(samples)
    #         self.all_digital.extend(digital)
    #     ppk2.stop_measuring()
    #     return
    
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

    def get_cmake_var(self,name):
        cache_path = self.BUILD_FOLDER + "/CMakeCache.txt"
        with open(cache_path) as f:
            for line in f:
                if line.startswith(f"{name}:"):
                    return line.split("=",1)[1].strip()
        return None
    def reCompile(self,compileFlags):
        print("Recompiling")
        cmd = ["wsl", "--cd", self.BUILD_FOLDER, "cmake"]
        for flag in compileFlags:
            cmd.append(flag)
        cmd.append("..")
        subprocess.run(cmd, check=True,capture_output=True)
        subprocess.run(["wsl", "--cd", self.BUILD_FOLDER, "make", "-j4"], check=True,capture_output=True)
        print("Finished Compiling")
        
    def evaluate(self,securityLevel,iterationCount=1000,baselineFreq=250,operation='All'):
        self.uart_init()
        self.ppk2_init(self.PPK2_PORT)
        #self.all_samples = []
        #self.all_digital = []
        #self.stop_sampling = threading.Event()
        #self.ppk2_logger_thread = threading.Thread(target=self.ppk2_logger, daemon=True)
        if(not self.ppk2.ser.is_open):
            print("PPK2 port was not open - opening")
            self.ppk2.ser.open()
            time.sleep(1)
        if(not self.uart.is_open):
            print("UART port was not open - opening")
            self.uart.open()
            time.sleep(1)
        #self.clearPPK2_buffer()
        
        
        match securityLevel:
            case 1 | 512:
                elf_file = 'MLKEM512'
            case 2 | 768:
                elf_file = 'MLKEM768'
            case 4 | 1024:
                elf_file = 'MLKEM1024'

        if operation != "All":
            elf_file = elf_file + "_" + operation + ".elf"
            elf_path = self.BUILD_FOLDER + elf_file
            elf_path = elf_path.replace("\\", "/")
            

        else:
            elf_file = elf_file + ".elf"
            elf_path = self.BUILD_FOLDER + "/" + elf_file
            elf_path = elf_path.replace("\\", "/")

        try:
            count = int(self.get_cmake_var("ITERATION_COUNT"))
            freq = int(self.get_cmake_var("BASELINE_AVERAGE_FREQ"))

            if count != iterationCount or freq != baselineFreq:
                print("IterationCount/baseline freq dont match compiled versions -- RECOMPILING")
                compileFlags = []
                compileFlags.append(f"-DITERATION_COUNT={iterationCount}")
                compileFlags.append(f"-DBASELINE_AVERAGE_FREQ={baselineFreq}")
                self.reCompile(compileFlags)

            #print(elf_path)
            

            #self.ppk2_logger_thread.start()
            #self.uart.read(1) #To catch uart initialization

            metrics = {}

            if operation == "All":
                metrics['gen'] = {
                    'cycles':[],
                    'stackUsage':0  
                }
                metrics['enc'] = {
                    'cycles':[],
                    'stackUsage':0  
                }
                metrics['dec'] = {
                    'cycles':[],
                    'stackUsage':0  
                }
            else:
                metrics[operation] = {
                    'cycles':[],
                    'stackUsage':0  
                }

            #Flash Board
            self.turnOnPico()
            self.dp.programBoard(elf_path)
            self.turnOffPico()
            self.uart.reset_input_buffer()
            time.sleep(0.05)
            self.turnOnPico()
            print(f"Running mlkem{securityLevel} {operation} {iterationCount} times ")

            for i in range(iterationCount):
                raw_bytes = self.uart.readline()  # Read until /n
                bytes = raw_bytes.decode("utf-8").strip()
                data = json.loads(bytes)


                if operation != "All":
                    opCycles = operation + "_cycles"
                    metrics[operation]['cycles'].append(data[opCycles] - data['overhead'])
                else:
                    metrics['gen']['cycles'].append(data['gen_cycles'] - data['overhead'])
                    metrics['enc']['cycles'].append(data['enc_cycles'] - data['overhead'])
                    metrics['dec']['cycles'].append(data['dec_cycles'] - data['overhead'])

                #Only execute once as stack use doesnt change
                if i == 1:
                    if operation != "All":
                        opStack = operation + "_stack"
                        metrics[operation]['stackUsage'] = data[opStack]
                    else:
                        metrics['gen']['stackUsage'] = data['gen_stack']
                        metrics['enc']['stackUsage'] = data['enc_stack']
                        metrics['dec']['stackUsage'] = data['dec_stack']
                

            # #Stop ppk2 sampling thread
            # self.stop_sampling.set()

            # #Wait till ppk2 thread finished
            # self.ppk2_logger_thread.join()


            # logicPorts = []
            # ops = []
            # print(self.gpioConfig)
            # #Logic Port Pins    
            # for i in range(0,8):
            #     i = str(i)
            #     if(i in self.gpioConfig):
                    
            #         lport = self.gpioConfig[i]
            #         op = lport['operation']
            #         logicPorts.append(i)
            #         ops.append(op)
            #         #gpioPin = lport['gpio']

            # opResults = self.proccessSamples(self.all_samples,self.all_digital,logicPorts,ops,iterationCount)
            
            opResults = {}
            if operation != "All":
                opResults = {
                    operation:{}   
                            }
                opResults[operation]['avg_cycles'] = sum(metrics[operation]["cycles"])/len(metrics[operation]["cycles"])
                opResults[operation]['stackUsage'] = metrics[operation]["stackUsage"]
            else:
                opResults = {
                        'gen':{},
                        'enc':{},
                        'dec':{}    
                }
                opResults['gen']['avg_cycles'] = sum(metrics['gen']["cycles"])/len(metrics['gen']["cycles"])
                opResults['enc']['avg_cycles'] = sum(metrics['enc']["cycles"])/len(metrics['enc']["cycles"])
                opResults['dec']['avg_cycles'] = sum(metrics['dec']["cycles"])/len(metrics['dec']["cycles"])
                #print(f"Sum of gen cycles is {sum(metrics['gen']["cycles"])}")
                #print(f"len of gen cycles is {len(metrics['gen']["cycles"])}")
                #print(f"avg of gen cycles is {sum(metrics['gen']["cycles"])/len(metrics['gen']["cycles"])}")

                opResults['gen']['stackUsage'] = metrics['gen']["stackUsage"]
                opResults['enc']['stackUsage'] = metrics['enc']["stackUsage"]
                opResults['dec']['stackUsage'] = metrics['dec']["stackUsage"]

            results = {
                "algorithm": "ML-KEM-" + str(securityLevel),
                **({"operation": operation} if operation != "All" else {}),
                "iterations": iterationCount,
                "baseline_freq": baselineFreq,
                **opResults,
            }
            #print("RESULTS:",results)

            outputFile = self.resultsFolder + "/mlkem" + str(securityLevel)
            if operation != "All":
                outputFile += "_" + operation
            outputFile += "-" + str(self.resultNum) + ".json"
            outputFile = outputFile.replace("\\", "/")
            
            with open(outputFile, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=4)
            
            self.resultNum += 1
            print("Saved Results to:",outputFile)
                
        except Exception as e:
            print(e)
            print("Error")
            self.ppk2.ser.close()
            return

        finally:
            self.uart.close()
            self.ppk2.ser.close()
        return results


    # def proccessSamples(self,samples,digitalSignals,logicPorts,ops,iterationCount,sampleRate=100000):
    #     '''
    #     inputs: samples,digitalSignals, logicPorts to monitor and operations related to logicPorts
    #     Outputs average energy for each signal in logicPorts
    #     '''
    #     print("PROCCESSING SAMPLES")
    #     d0 = 1
    #     d1 = 2
    #     d2 = 4
    #     d3 = 8
    #     d4 = 16

    #     #FILTER out samples where GPIO pin is not HIGH
    #     all_samples = [(s, d) for s, d in zip(samples, digitalSignals) if d > 0]
    #     for s,d in all_samples:
    #         if(s) < 0:
    #             print("NEGATIVE READINGS")
    #     print("LEN SAMPLES:",len(samples))
    #     currentReadings = {}
    #     for logicPort in logicPorts:
    #         currentReadings[str(2**int(logicPort))] = []
        
    #     for sample, digital in all_samples:
    #         currentReadings[str(digital)].append(sample)

    #     print(currentReadings.keys())
    #     opCount = 0
    #     print(len(currentReadings['8']))
    #     avgBaslineI = sum(currentReadings['8'])/len(currentReadings['8'])

    #     energyUsage = {}

    #     for dPin in currentReadings:
    #         if dPin == '8':
    #             continue
    #         sumI = sum(currentI - avgBaslineI for currentI in currentReadings[dPin])
    #         energyUse_mJ = (self.VOLTAGE * sumI * (1/sampleRate))/1000
    #         energyUse_mJ /= iterationCount
    #         print(ops[opCount],"used",energyUse_mJ,"mJ")
    #         print(ops[opCount],"had avergae current:",sumI/len(currentReadings[dPin]))
    #         print(ops[opCount],"had avergae current before basline:",sum(currentReadings[dPin])/len(currentReadings[dPin]))
    #         energyUsage[ops[opCount]] = {
    #             'avg_energy_mJ':energyUse_mJ
    #         }
    #         opCount += 1
    #     print("Average baseline:",avgBaslineI)
    #     return energyUsage


# build = r"\\wsl.localhost\Ubuntu\home\seanh\College\FYP\PicoW\build"
# result = r"\\wsl.localhost\Ubuntu\home\seanh\College\FYP\PicoW\results"

# eval = mlkemEvaluator('PicoW',"COM12",3.3,"COM16",115200,build,result)

# config = {
#     "0":{
#         "operation":"gen",
#         "gpio":13
#     },
#     "1":{
#         "operation":"enc",
#         "gpio":12
#     },
#     "2":{
#         "operation":"dec",
#         "gpio":14 
#     },
#     "3":{
#         "operation":"baseline",
#         "gpio":15
#     }
# }

# eval.configureGPIO(config)
# eval.evaluate(512,100,25)








