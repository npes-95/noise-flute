# midi test

import mido

mido.set_backend(
    'mido.backends.rtmidi/MACOSX_CORE'
)

print("Using: ", mido.backend)

with mido.open_input(
    'USB MIDI keyboard'
    #virtual=True
) as mip:
    for mmsg in mip:
        print(mmsg.type)
        print(mmsg.bytes())
