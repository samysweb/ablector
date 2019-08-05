import logging

class AblectorConfig:
    def __init__(self):
        self.omittedStages = {}
        self.logLevel = logging.INFO
        self.timeOffset = 0
        self.ufReuseFactor=0

    def setUfReuseFactor(self, factor):
        self.ufReuseFactor = factor
    
    def omitStage(self, op, num):
        if op not in self.omittedStages:
            self.omittedStages[op] = {}
        self.omittedStages[op][num] = True
    
    def isOmitted(self, op, num):
        return (op in self.omittedStages) and (num in self.omittedStages[op])

    def setDebugLogLevel(self):
        self.logLevel = logging.DEBUG

    def getLogLevel(self):
        return self.logLevel

    def addTimeOffset(self, offset):
        self.timeOffset+=offset

    def getTimeOffset(self):
        return self.timeOffset

    