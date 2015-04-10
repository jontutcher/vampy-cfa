import numpy,vampy
from yaafelib import *
from vampy import *

class PyCFA: 
	def __init__(self,inputSampleRate): 
		self.m_inputSampleRate = inputSampleRate 
		self.m_stepSize = 0
		self.m_blockSize = 0
		self.m_channels = 0
		self.previousSample = 0.0
		self.threshold = 0.005
		self.counter = 0
		
	def initialise(self,channels,stepSize,blockSize):
		self.m_channels = channels
		self.m_stepSize = stepSize		
		self.m_blockSize = blockSize

		# set feature plan at startup
		self.fp = FeaturePlan(sample_rate=self.m_inputSampleRate)
		self.fp.addFeature('cfa: ContinuousFrequencyActivation '\
		'BinThreshold=0.1  FFTLength=0 FFTWindow=Hanning  NbPeaks=5 '\
		'NbRunAvgFrames=21 NbSumFrames=100  NormWindow=Hanning '\
		'StepNbSumFrames=50 blockSize={0} stepSize={1}'.format(blockSize, stepSize))
		self.engine = Engine()
		self.engine.load(self.fp.getDataFlow())
		self.engine.reset()
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
		output0={
		'identifier':'cfa',
		'name':'Continuous Frequency Activation',
		'description':'Continuously (over several seconds) activated '\
				'frequency bands are detected and their spectral peak values '\
				'summed up to the CFA-value',
		'unit':' ',
		'hasKnownExtents':False,
		'isQuantized':False,
		'sampleType':'VariableSampleRate'
		}

		return [output0]


	def getParameterDescriptors(self):
		paramlist1={
		'identifier':'threshold',
		'name':'Noise threshold',
		'description':'',
		'unit':'v',
		'minValue':0.0,
		'maxValue':0.5,
		'defaultValue':0.005,
		'isQuantized':False
		}
		return [paramlist1]


	def setParameter(self,paramid,newval):
		if paramid == 'threshold' :
			self.threshold = newval
		return

		
	def getParameter(self,paramid):
		if paramid == 'threshold' :
			return self.threshold
		else:
			return 0.0


	# legacy process type: the input is a python list of samples
	def process(self,inbuf,timestamp):
		self.engine.writeInput('audio', numpy.array(inbuf))
		self.engine.process()
		return []

	def getRemainingFeatures(self):
		outputFeatureSet = FeatureSet()
		outputFeatureSet[0] = flist = FeatureList()
		self.engine.flush()
		feats = self.engine.readAllOutputs()
		featlength=50*self.m_stepSize	# 50 is the number of sub frames in Yaafe CFA
		output0=[]
		results = feats['cfa'].tolist()
		for i in range(len(results)):
			f = Feature()
			f.hasTimestamp = True
			f.timestamp = frame2RealTime(featlength*i,self.m_inputSampleRate)
			f.values = [results[i]]
			flist.append(f)	
		return outputFeatureSet
