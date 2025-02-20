import optiPython as oP
import json
import sys
import matplotlib.pyplot as plt
from pathlib import Path

# # JSON string
# triInfo = '{"x0": [9.01006524, -4.739905], "T0": 25.887855886616833, "grad0": [0.62334049, 0.78195053], "x1": [ 8.91006524, -4.539905  ], "T1": 25.995574287564278, "grad1": [0.4539905 , 0.89100652], "xHat": [ 9.53879533, -3.97683432], "listIndices": [1.0, 1.0, 1.0, 1.452, 1.0], "listxk": [ [ 9.01006524, -4.739905  ], [ 8.91006524, -4.539905  ], [ 9.23879533, -3.82683432], [ 9.53879533, -3.97683432] ], "listB0k": [ [-0.1,  0.2], [0.22873008, 0.91307067], [0.52873008, 0.76307067] ], "listBk": [ [-0.1,  0.2], [0.22873008, 0.91307067], [0.52873008, 0.76307067] ], "listBkBk1": [ [0.4022869, 0.7895325], [0.33910078, 0.8186617 ], [ 0.3 , -0.15], [ 0.3 , -0.15] ], "plotBefore": 1, "plotAfter": 1, "plotOpti": 1 } '


with open(Path(sys.argv[1])) as f:
    triInfo = f.readline()
    print(triInfo)
    params_dict = json.loads(triInfo)
    nRegions = len(params_dict['listxk']) -2
    triFan = oP.triangleFan(nRegions) # initialize a triangle fan
    dict_out = triFan.outputJSON(triInfo)
    # try:
    #     dict_out = triFan.outputJSON(triInfo)
    # except:
    #     import ipdb; ipdb.set_trace()
    print(dict_out["THat"], ", ", dict_out["gradHat"][0], ", ", dict_out["gradHat"][1])
    #str_out = json.dumps(dict_out)
    #print(str_out)



# # Read input from C
# triInfo = open('/Users/marianamartinez/Documents/Curvy-JMM/JMM/update.json', 'r')

# # Call function with arguments
# dict_out = triFan.outputJSON(triInfo)


# # serialize output data as JSON and write to stdout
# with open('/Users/marianamartinez/Documents/Curvy-JMM/JMM/updateSolve.json', 'w') as f:
#     json.dump(dict_out, f)

# if(dict_out["plotAfter"] == 1):
#     plt.show()


triInfo = '{"x0": [-0.37391193999999999820, 9.99300704999999922507], "T0": 26.61562288646399920822, "grad0": [1.447184, 0.090325], "x1": [-0.87155742999999996634, 9.96194698000000045113], "T1": 25.89263281813499872897, "grad1": [0.99623846212500000163, 0.08665406270200000372], "xHat": [-0.18578123999999998639, 10.64573174000000044259], "listIndices": [1.00000000000000000000,1.00000000000000000000,1.00000000000000000000],"listxk": [[-0.37391193999999999820, 9.99300704999999922507],[-0.87155742999999996634, 9.96194698000000045113],[-0.18578123999999998639, 10.64573174000000044259]],"listB0k": [[-0.49826515999999998474, -0.01864377000000000048],[0.00000000000000000000, 0.00000000000000000000]],"listBk": [[-0.49671646000000002630, -0.04345705999999999875],[0.00000000000000000000, 0.00000000000000000000]],"listBkBk1": [[0.00000000000000000000, 0.00000000000000000000],[0.00000000000000000000, 0.00000000000000000000]],"plotBefore": 0, "plotAfter": 0, "plotOpti": 0}'
