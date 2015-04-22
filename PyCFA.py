import numpy
import vampy
from yaafelib import *
from vampy import *


class PyCFA:
    """
    VamPy wrapper around 'cba-yaafe-extension'
    continuous frequencyactivation plugin
    """

    def __init__(self, inputSampleRate):
        self.m_inputSampleRate = inputSampleRate
        self.m_stepSize = 0
        self.m_blockSize = 0
        self.m_channels = 0
        self.previousSample = 0.0
        self.counter = 0
        params = self.getParameterDescriptors()
        for param in params:
            setattr(self, param['identifier'], param['defaultValue'])

    def initialise(self, channels, stepSize, blockSize):
        self.m_channels = channels
        self.m_stepSize = stepSize
        self.m_blockSize = blockSize

        # set feature plan at startup based on defaults
        self.setFeaturePlan()
        return True

    def getMaker(self):
        return 'BBC'

    def getName(self):
        return 'Continuous Frequency Activation'

    def getIdentifier(self):
        return 'vampy-cfa'

    def getMaxChannelCount(self):
        return 1

    def getInputDomain(self):
        return 'TimeDomain'

    def getOutputDescriptors(self):
        #descriptors can be returned as python dictionaries
        output0 = {
            'identifier': 'cfa',
            'name': 'Continuous Frequency Activation',
            'description': 'Continuously (over several seconds) activated '
                    'frequency bands are detected and their spectral peak '
                    'values summed up to the CFA-value',
            'unit': ' ',
            'hasKnownExtents': False,
            'isQuantized': False,
            'sampleType': 'VariableSampleRate'
        }

        return [output0]

    def setParameter(self, paramid, newval):
        if paramid in list(param['identifier']
                           for param in self.getParameterDescriptors()):
            setattr(self, paramid, newval)

        # update feature plan if necessary
        self.setFeaturePlan()
        return

    def getParameter(self, paramid):
        if paramid in list(param['identifier']
                           for param in self.getParameterDescriptors()):
            return getattr(self, paramid)
        else:
            return 0.0

    # legacy process type: the input is a python list of samples
    def process(self, inbuf, timestamp):
        self.engine.writeInput('audio', numpy.array(inbuf))
        self.engine.process()
        self.counter += self.m_stepSize
        return []

    def getRemainingFeatures(self):
        outputFeatureSet = FeatureSet()
        outputFeatureSet[0] = flist = FeatureList()
        self.engine.flush()
        feats = self.engine.readAllOutputs()
        results = feats['cfa'].tolist()
        featlength = self.counter / len(results)
        for i in range(len(results)):
            f = Feature()
            f.hasTimestamp = True
            f.timestamp = frame2RealTime(int(featlength * i),
                                         self.m_inputSampleRate)
            f.values = [results[i]]
            flist.append(f)
        return outputFeatureSet

    def setFeaturePlan(self):
        # prevent changing features if we don't yet have a step/block size
        if self.m_stepSize <= 0:
            return
        if self.m_blockSize <= 0:
            return
        # build new feature plan
        self.fp = FeaturePlan(sample_rate=self.m_inputSampleRate)
        self.fp.addFeature('cfa: ContinuousFrequencyActivation '
                           'BinThreshold={0:.2f}  FFTLength=0 '
                           'FFTWindow=Hanning NbPeaks={1:.0f} '
                           'NbRunAvgFrames={2:.0f} NbSumFrames={3:.0f} '
                           'NormWindow=Hanning StepNbSumFrames={4:.0f} '
                           'blockSize={5:.0f} stepSize={6:.0f}'.format(
                               self.binThreshold,
                               self.peaks,
                               self.runAvgFrames,
                               self.sumFrames,
                               self.stepFrames,
                               self.m_blockSize,
                               self.m_stepSize))
        self.engine = Engine()
        self.engine.load(self.fp.getDataFlow())
        self.engine.reset()
        return

    def getParameterDescriptors(self):
        return [
            {
                'identifier': 'binThreshold',
                'name': 'Bin Threshold',
                'description': 'Values less than BinThreshold '
                'will be set to 0, others to 1',
                'minValue': 0.0,
                'maxValue': 1,
                'defaultValue': 0.1,
                'isQuantized': False
            },
            {
                'identifier': 'peaks',
                'name': 'Peaks',
                'description': 'Number of peaks to find',
                'minValue': 1,
                'maxValue': 20,
                'defaultValue': 5,
                'isQuantized': True,
                'quantizeStep': 1.0
            },
            {
                'identifier': 'runAvgFrames',
                'name': 'Running Average Frames',
                'description': 'Number of frames to integrate '
                'for running average',
                'minValue': 1,
                'maxValue': 1000,
                'defaultValue': 21,
                'isQuantized': True,
                'quantizeStep': 1.0
            },
            {
                'identifier': 'sumFrames',
                'name': 'Summing Frames',
                'description': 'Number of FFT frames to sum up',
                'minValue': 1,
                'maxValue': 500,
                'defaultValue': 100,
                'isQuantized': True,
                'quantizeStep': 1.0
            },
            {
                'identifier': 'stepFrames',
                'name': 'Step Size',
                'description': 'Step between consecutive frames',
                'minValue': 1,
                'maxValue': 1000,
                'defaultValue': 512,
                'isQuantized': True,
                'quantizeStep': 1.0
            }]
