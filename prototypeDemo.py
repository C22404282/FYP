from entropyEvaluator import entropyEvaluator
from mlkem_evaluator import mlkemEvaluator
import numpy as np




buildFolder = r"\\wsl.localhost\Ubuntu\home\seanh\College\FYP\PicoW\build"

mlkem_result = r"\\wsl.localhost\Ubuntu\home\seanh\College\FYP\PicoW\mlkemResults"

entropy_dataset = r"\\wsl.localhost\Ubuntu\home\seanh\College\FYP\PicoW\entropyDatasets"
entropy_result = r"\\wsl.localhost\Ubuntu\home\seanh\College\FYP\PicoW\entropyResults"


nist_path = r"\\wsl.localhost\Ubuntu\home\seanh\College\FYP/SP800-90B_EntropyAssessment/cpp"

PPK2_PORT = "COM12"
VOLTAGE = 3.3
UART_PORT = 'COM16'
BAUD_RATE = 115200

targetBoard = "PicoW"
# mlkem_eval = mlkemEvaluator(PPK2_PORT,VOLTAGE,UART_PORT,baud_rate=BAUD_RATE,buildFolder,mlkem_result,targetBoard=targetBoard)
# mlkem_eval.evaluate(512,1000,2500,"All")


# mlkem512_avgCycles = {
#     'gen':[],
#     'enc':[],
#     'dec':[]
# }
# mlkem768_avgCycles = {
#     'gen':[],
#     'enc':[],
#     'dec':[]
# }
# mlkem1024_avgCycles = {
#     'gen':[],
#     'enc':[],
#     'dec':[]
# }

# for i in range(10):
#     results = mlkem_eval.evaluate(512,1000,2500,"All")
#     mlkem512_avgCycles['gen'].append(results['gen']['avg_cycles'])
#     mlkem512_avgCycles['enc'].append(results['enc']['avg_cycles'])
#     mlkem512_avgCycles['dec'].append(results['dec']['avg_cycles'])

# for i in range(10):
#     results = mlkem_eval.evaluate(768,1000,2500,"All")
#     mlkem768_avgCycles['gen'].append(results['gen']['avg_cycles'])
#     mlkem768_avgCycles['enc'].append(results['enc']['avg_cycles'])
#     mlkem768_avgCycles['dec'].append(results['dec']['avg_cycles'])

# for i in range(10):
#     results = mlkem_eval.evaluate(1024,1000,2500,"All")
#     mlkem1024_avgCycles['gen'].append(results['gen']['avg_cycles'])
#     mlkem1024_avgCycles['enc'].append(results['enc']['avg_cycles'])
#     mlkem1024_avgCycles['dec'].append(results['dec']['avg_cycles'])

# data = mlkem512_avgCycles['gen']
# mean = np.mean(data)
# std = np.std(data, ddof=0)
# rstd = (std / mean) * 100
# print("MLKEM512_GEN - RSTD:",rstd)

# data = mlkem512_avgCycles['enc']
# mean = np.mean(data)
# std = np.std(data, ddof=0)
# rstd = (std / mean) * 100
# print("MLKEM512_ENC - RSTD:",rstd)

# data = mlkem512_avgCycles['dec']
# mean = np.mean(data)
# std = np.std(data, ddof=0)
# rstd = (std / mean) * 100
# print("MLKEM512_DEC - RSTD:",rstd)

# data = mlkem768_avgCycles['gen']
# mean = np.mean(data)
# std = np.std(data, ddof=0)
# rstd = (std / mean) * 100
# print("MLKEM768_GEN - RSTD:",rstd)

# data = mlkem768_avgCycles['enc']
# mean = np.mean(data)
# std = np.std(data, ddof=0)
# rstd = (std / mean) * 100
# print("MLKEM768_ENC - RSTD:",rstd)

# data = mlkem768_avgCycles['dec']
# mean = np.mean(data)
# std = np.std(data, ddof=0)
# rstd = (std / mean) * 100
# print("MLKEM768_DEC - RSTD:",rstd)

# data = mlkem1024_avgCycles['gen']
# mean = np.mean(data)
# std = np.std(data, ddof=0)
# rstd = (std / mean) * 100
# print("MLKEM1024_GEN - RSTD:",rstd)

# data = mlkem1024_avgCycles['enc']
# mean = np.mean(data)
# std = np.std(data, ddof=0)
# rstd = (std / mean) * 100
# print("MLKEM1024_ENC - RSTD:",rstd)

# data = mlkem1024_avgCycles['dec']
# mean = np.mean(data)
# std = np.std(data, ddof=0)
# rstd = (std / mean) * 100
# print("MLKEM1024_DEC - RSTD:",rstd)



# results = mlkem_eval.evaluate(768,1000,2500,"All")
# print("RESULTS")
# mlkem_eval.printResults(results)


# results = mlkem_eval.evaluate(1024,1000,2500,"All")
# print("RESULTS")
# mlkem_eval.printResults(results)


entropy_eval = entropyEvaluator(targetBoard,PPK2_PORT,VOLTAGE,UART_PORT,BAUD_RATE,buildFolder,entropy_dataset,entropy_result,nist_path)

entropy_eval.evaluate()

