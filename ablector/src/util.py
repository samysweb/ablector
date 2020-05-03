import numpy as np

def NotStr(inputStr):
    return ''.join([ ('0' if c == '1' else '1') for c in inputStr])

def Bin2Int(inputStr, unsigned=False):
    """compute the 2's complement of int value val"""
    if not unsigned:
        if inputStr[0] == '1': # if sign bit is set e.g., 8bit: 128-255
            inputStr = NotStr(inputStr) # compute not
            return -(int(inputStr,2)+1)
        return int(inputStr, 2)
    else:
        return int(inputStr,2)

def Int2Bin(inputInt, width):
    return np.binary_repr(inputInt, width)