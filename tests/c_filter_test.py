import numpy as np
import math
import scipy.io.wavfile
from scipy import signal
import matplotlib.pyplot as plt
import pylab
from Filter import IIR


class AudioBuffer:

    def __init__(self,length=2048):
        self.length = length
        self.buffer = np.zeros(length)

    def write(self,data):
        if len(data) <= self.length:
            self.buffer = data
        else:
            print("Buffer overflow.")

    def writeElement(self,data,element_no):
        self.buffer[element_no] = data

    def read(self):
        return self.buffer

    def readElement(self, element_no):
        return self.buffer[element_no]

class AudioInterface:

    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate

    def genWav(self,file_name, array):
        #16 bit int is -32768 to 32767 (because of 0 value)
        convert_16_bit = float((2**15)-1)

        # scale to -1.0 -- 1.0
        array = array / np.amax(array)

        #convert to 16 bit int
        samples = np.int16(array*convert_16_bit)

        #write to .wav file
        scipy.io.wavfile.write(file_name,self.sample_rate,samples)

class Counter:

    def __init__(self, increment_value=2048):
        self.increment_value = increment_value
        self.x = 0

    def getNext(self):
        y = self.x
        self.x = self.x + self.increment_value
        return y

    def reset(self):
        self.x = 0
        return self.x



class Oscillator:

    def __init__(self,freq=440,sample_rate=44100):
        self.freq = freq
        self.sample_rate = sample_rate

        self.phase_acc = 0
        self.phase_inc = 2*np.pi*freq/sample_rate

        self.k = math.cos(2*np.pi*self.freq/self.sample_rate)

        self.init_sample1 = 0
        self.init_sample2 = math.sin(2*np.pi*self.freq/self.sample_rate)

    def setFreq(self,freq):

        #recalculate phase increment for new freq
        self.freq = freq
        self.phase_inc = 2*np.pi*self.freq/sample_rate

        #calculate constant
        self.k = math.cos(2*np.pi*self.freq/self.sample_rate)

        #first two sample for new frequency have the same phase as the old signal
        self.init_sample1 = math.sin(self.phase_acc)
        self.init_sample2 = math.sin(self.phase_acc+self.phase_inc)

        #compensate for first two sample's generation
        self.phase_acc += 2*self.phase_inc


    def gen(self,buflen,sig_type):
        output = np.zeros(buflen)

        if sig_type == "sine":

            output[0] = self.init_sample1
            output[1] = self.init_sample2

            for i in range (2,buflen):

                if self.phase_acc >= 2*np.pi:

                    self.phase_acc -= 2*np.pi

                output[i] = 2*self.k*output[i-1] - output[i-2]

                self.phase_acc += self.phase_inc

            self.init_sample1 = output[buflen-2]
            self.init_sample2 = output[buflen-1]

        else:

            output = 2*np.random.random(buflen) - 1

        return output



class Sine(Oscillator):
    def gen(self,buflen):
        return Oscillator.gen(self,buflen,"sine")

class Noise(Oscillator):
    def gen(self,buflen):
        return Oscillator.gen(self,buflen,"noise")


#################### MAIN ####################
buffer_length = 2048
freq = 1500
sample_rate = 44100
sig_length_seconds = 0.1


#wn = 2*math.pi*freq/sample_rate
#b, a = signal.iirdesign(wn, wn-0.1, 3, 80, False, 'ellip')

b, a = signal.iirdesign([0.2,0.21], [0.1,0.3], 0.1, 110)


out = AudioInterface(sample_rate)
buf = AudioBuffer(buffer_length)
cnt = Counter(buffer_length)
filt = IIR(a,b)

print("\nCREATING NOISE GENERATOR")
mknoise = Noise()

final_array = np.array([])

burst_length = cnt.getNext()

while sig_length_seconds != 0:

    sig_length_seconds = float(input("Choose burst length (seconds): "))


    while burst_length < sig_length_seconds*sample_rate:

        #generate wave into buffer
        buf.write(mknoise.gen(buffer_length))

        #concatenate buffer into final output array
        final_array = np.append(final_array,buf.read())

        burst_length = cnt.getNext()


    burst_length = cnt.reset()


if len(final_array) > 0:

    filt.iir_a(final_array)


    out.genWav("filter_noise_gen.wav",final_array)
    print("\n.wav file generated :)\n")

    #plot spectrum of filtered signal
    plt.psd(final_array)
    #plt.plot(final_array)
    plt.show()

else:

    print("\nNo signal was generated.\n")
