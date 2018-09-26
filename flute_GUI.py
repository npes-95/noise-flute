 SAMPLE_RATE = 44100
AUDIO_CHANS = 1
SAMPLE_SIZE = 16
CTRL_INTERVAL = 100 # milliseconds of audio

import sys
import mido
import numpy as np

from ADSR import ADSR
from scipy import signal
from Filter import IIR

from PyQt5.QtCore import QByteArray, QIODevice, QObject, QThread, Qt, pyqtSlot, pyqtSignal
from PyQt5.QtMultimedia import QAudioFormat, QAudioOutput
from PyQt5.QtWidgets import QApplication, QWidget, QSlider, QPushButton, QMessageBox, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox

# ----- MIDI -----

class MidiPortReader(QObject):

    # Create a signal for when a
    # MIDI note_on happens
    newNoteFrequency = pyqtSignal(float)
    newNoteVelocity = pyqtSignal(int)
    portClosed = pyqtSignal()

    # Object initialisation:
    def __init__(self):
        QObject.__init__(self)

        mido.set_backend(
            'mido.backends.rtmidi/MACOSX_CORE'
        )

        print("\n~~~~ MIDI ~~~~")
        print("Backend: ", mido.backend)

        # detect whether user has tried to change devices
        self.newDevice = False


        # the midi devices must have different names for this to work
        if not mido.get_output_names():
            self.MIDI_in = "Virtual Port"
            self.isVirtual = True
            print("No MIDI device detected, using Virtual Port")
        else:
            # set midi port name to that of the first port available
            self.MIDI_in = str(mido.get_output_names()[0])
            self.isVirtual = False
            print("Device:", self.MIDI_in)



    def getMIDIDevices(self):
        return mido.get_output_names() + ["Virtual Port"]

    def setMIDIDevice(self, dev):
        self.MIDI_in = dev
        self.newDevice = True

        if dev == "Virtual Port":
            self.isVirtual = True
        else:
            self.isVirtual = False


    # Define a function which is to
    # run in its own thread
    def listener(self):
        while(True):

            if not mido.get_output_names():
                self.MIDI_in = "Virtual Port"
                self.isVirtual = True

            with mido.open_input(self.MIDI_in,virtual=self.isVirtual) as mip:

                #get messages but also check whether user has changed the port
                while(self.newDevice == False and mido.get_output_names()):

                    for mmsg in mip.iter_pending():
                        print(mmsg.type)
                        print("freq: ", self.mtof(mmsg.bytes()[1]))

                        # Only communicate via the Qt signal
                        # Qt will stop us hurting ourselves
                        self.newNoteFrequency.emit(self.mtof(mmsg.bytes()[1]))
                        self.newNoteVelocity.emit(mmsg.bytes()[2])

                # stop playing note once midi connection is over, say that port is closed, so GUI can rescan for midi devices
                self.newNoteVelocity.emit(0)
                self.portClosed.emit()
                self.newDevice = False



    def mtof(self, note):
        return 2**((note-69)/12)*440




# ----- AUDIO -----


class Flute(QIODevice):

    SAMPLES_PER_READ = 1024
    CONVERT_16_BIT = float((2**15)-1)

    def __init__(self, format, parent = None):
        QIODevice.__init__(self, parent)
        self.data = QByteArray()

        # find bandwith for one hertz
        self.bdw = 2*np.pi/SAMPLE_RATE

        # start off with no note playing (toggled when we detect midi messages)
        self.note_on = 0

        # add freq offset so we can tune keys
        self.octave = 0


        # create Filter
        b, a = signal.iirdesign([0.2,0.21], [0.1,0.3], 3, 80, False, 'butter')
        self.filter = IIR(a,b)

        # create ADSR env. generator
        self.env = ADSR()
        self.env.setAttackRate(.1 * SAMPLE_RATE)
        self.env.setDecayRate(.3 * SAMPLE_RATE)
        self.env.setReleaseRate(5 * SAMPLE_RATE)
        self.env.setSustainLevel(.8)

        print("\n~~~~ GENERATOR ~~~~")

        # Check we can deal with the supplied
        # sample format. We're supposed to be
        # able to deal with any requested
        # sample format. But this is a
        # _minimal_ example, right?
        if format.isValid() and \
           format.sampleSize() == 16 and \
           format.byteOrder() == \
                QAudioFormat.LittleEndian and \
           format.sampleType() == \
                QAudioFormat.SignedInt and \
           format.channelCount() == 1 :
               print(
                 "Sample format compatible."
               )
               self.format = format


    def start(self):
        # Call QIODevices open
        # making this object readable
        self.open(QIODevice.ReadOnly)

    def playNote(self):
        self.note_on = 1
        self.env.gate(True)

    def stopNote(self):
        self.note_on = 0
        self.env.gate(False)

    def setOctave(self, octv):
        self.octave = octv

    def generateData(self, format, samples):
        tone = (2*np.random.random(samples) - 1)

        # call our filter and envelope c++ methods
        self.filter.iir_a(tone)
        self.env.process_a(tone)

        return np.int16(Flute.CONVERT_16_BIT*tone).tostring()


    def readData(self, bytes):
        if bytes > 2 * Flute.SAMPLES_PER_READ:
            bytes = 2 * Flute.SAMPLES_PER_READ
        return self.generateData(self.format,
                                 bytes//2)

    def updateFilter(self, freq):
        #recalculate filter coeffs based on new frequency
        freq *= 2**self.octave
        w = 2*np.pi*freq/SAMPLE_RATE

        if w<10*self.bdw:
            b, a = signal.iirdesign(w, w+10*self.bdw, 3, 80, False, 'cheby1')

        elif w>1-10*self.bdw:
            b, a = signal.iirdesign(w, w-10*self.bdw, 3, 80, False, 'cheby1')

        else:
            b, a = signal.iirdesign([w-10*self.bdw,w+10*self.bdw], [w-20**self.bdw,w+20**self.bdw], 3, 80, False, 'cheby1')

        self.filter.updatecoef(a,b)


    def updateADSR(self, a, d, s, r):
        self.env.setAttackRate(a * SAMPLE_RATE)
        self.env.setDecayRate(d * SAMPLE_RATE)
        self.env.setSustainLevel(s)
        self.env.setReleaseRate(r * SAMPLE_RATE)




# ----- GUI -----

class ToneGenerator(QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        super().__init__(parent)

        # start new thread that constantly polls MIDI input
        self.create_MIDI()

        # create GUI (windows, slider, etc...)
        self.create_UI(parent)

        format = QAudioFormat()
        self.create_AUDIO(format)
        self.generator = Flute(format, self)
        self.generator.start()
        self.output.start(self.generator)


    def create_AUDIO(self, format):
        format.setChannelCount(AUDIO_CHANS)
        format.setSampleRate(SAMPLE_RATE)
        format.setSampleSize(SAMPLE_SIZE)
        format.setCodec("audio/pcm")
        format.setByteOrder(
            QAudioFormat.LittleEndian
        )
        format.setSampleType(
            QAudioFormat.SignedInt
        )

        self.output = QAudioOutput(format, self)
        output_buffer_size = \
            int(2*SAMPLE_RATE \
                 *CTRL_INTERVAL/1000)
        self.output.setBufferSize(
            output_buffer_size
        )

    def create_MIDI(self):
        # Create the port reader object
        self.midiListener = MidiPortReader()

        # Create a thread which will read it
        self.listenerThread = QThread()

        # Take the object and move it
        # to the new thread (it isn't running yet)
        self.midiListener.moveToThread(self.listenerThread)

        # Tell Qt the function to call
        # when it starts the thread
        self.listenerThread.started.connect(self.midiListener.listener)

        # connect pyqtSignals to slots in ToneGenerator
        self.midiListener.newNoteFrequency.connect(self.on_newNoteFrequency)
        self.midiListener.newNoteVelocity.connect(self.on_newNoteVelocity)
        self.midiListener.portClosed.connect(self.on_portClosed)


        # Fingers in ears, eyes tight shut...
        self.listenerThread.start()

        # Good grief, IT WORKS!




    def create_UI(self, parent):
        # Create a slider to fine tune freq and two buttons
        #self.octaveBox = QSlider(Qt.Horizontal)
        #self.octaveBox.setMinimum(-100)
        #self.octaveBox.setMaximum(100)
        self.octaveBox = QSpinBox()
        self.octaveBox.setRange(-5,5)

        self.octaveLabel = QLabel("Octave: ")
        self.quitButton = QPushButton(self.tr('&Quit'))

        # create dropdown menu so user can choose midi device in use (populate list from data from midi listener object)
        self.MIDIMenu = QComboBox()
        self.MIDIMenu.addItems(self.midiListener.getMIDIDevices())

        # create ADSR sliders
        self.aSlider = QSlider(Qt.Vertical)
        self.aSlider.setMinimum(1)
        self.aSlider.setMaximum(50)
        self.aSlider.setSliderPosition(1)

        self.dSlider = QSlider(Qt.Vertical)
        self.dSlider.setMinimum(1)
        self.dSlider.setMaximum(50)
        self.dSlider.setSliderPosition(8)

        self.sSlider = QSlider(Qt.Vertical)
        self.sSlider.setMinimum(1)
        self.sSlider.setMaximum(100)
        self.sSlider.setSliderPosition(80)

        self.rSlider = QSlider(Qt.Vertical)
        self.rSlider.setMinimum(1)
        self.rSlider.setMaximum(100)
        self.rSlider.setSliderPosition(50)


        # No parent: we're going to add this
        # to vLayout.
        hLayout1 = QHBoxLayout()
        hLayout1.addWidget(self.octaveLabel)
        hLayout1.addWidget(self.octaveBox)

        hLayout2 = QHBoxLayout()
        hLayout2.addWidget(self.aSlider)
        hLayout2.addWidget(self.dSlider)
        hLayout2.addWidget(self.sSlider)
        hLayout2.addWidget(self.rSlider)

        hLayout3 = QHBoxLayout()
        hLayout3.addWidget(self.MIDIMenu)
        hLayout3.addWidget(self.quitButton)


        # parent = self: this is the
        # "top level" layout
        vLayout = QVBoxLayout(self)
        vLayout.addLayout(hLayout1)
        vLayout.addLayout(hLayout2)
        vLayout.addLayout(hLayout3)

        # connect qt object signals to slots

        self.quitButton.clicked.connect(self.quitClicked)
        self.octaveBox.valueChanged.connect(self.changeOctave)
        self.aSlider.valueChanged.connect(self.changeADSRParam)
        self.dSlider.valueChanged.connect(self.changeADSRParam)
        self.sSlider.valueChanged.connect(self.changeADSRParam)
        self.rSlider.valueChanged.connect(self.changeADSRParam)
        self.MIDIMenu.currentIndexChanged[str].connect(self.changeMIDIDevice)

    # this isn't a @pyqtSlot(), the text is passed directly to the function
    def changeMIDIDevice(self, dev):
        self.midiListener.setMIDIDevice(dev)


    @pyqtSlot()
    def quitClicked(self):
        self.close()

    @pyqtSlot()
    def changeOctave(self):
        #scale slider value to freq and pass to subclass to update filter
        self.generator.setOctave(self.octaveBox.value())

    @pyqtSlot(float)
    def on_newNoteFrequency(self, freq):
        # change value of filter cutoff so it sounds like we're playing a different note
        self.generator.updateFilter(freq)

    @pyqtSlot(int)
    def on_newNoteVelocity(self, value):
        # note_off message doesn't work with shit USB keyboards, so we simulate a note_off message with the velocity
        if value != 0:
            self.generator.playNote()
        else:
            self.generator.stopNote()

    @pyqtSlot()
    def on_portClosed(self):
        # when port has closed, clear drop down menu and rescan for MIDI devices
        self.MIDIMenu.clear()
        self.MIDIMenu.addItems(self.midiListener.getMIDIDevices())


    @pyqtSlot()
    def changeADSRParam(self):
        self.generator.updateADSR(self.aSlider.value()/10, self.dSlider.value()/10, self.sSlider.value()/100, self.rSlider.value()/10)






if __name__ == "__main__":

    app = QApplication(sys.argv)
    window = ToneGenerator()
    window.show()
    sys.exit(app.exec_())
