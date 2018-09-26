import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

freq = 1500
SAMPLE_RATE = 44100

w = 2*np.pi*freq/SAMPLE_RATE
bdw = 2*np.pi/SAMPLE_RATE


b, a = signal.iirdesign([w-10*bdw,w+10*bdw], [w-20**bdw,w+20**bdw], 3, 120, False, 'cheby1')
#b, a = signal.iirdesign([w-0.2,w+0.2], [w-0.3,w+0.3], 3, 120, False, 'butter')

w, h = signal.freqz(b,a)
plt.plot(w, abs(h))
plt.show()
