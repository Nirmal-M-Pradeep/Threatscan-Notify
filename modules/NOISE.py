import os
import noisereduce as nr
from pydub import AudioSegment
import numpy as np
import scipy.io.wavfile as wav 

def Noise(file_path):

    try:
        audio=AudioSegment.from_file(file_path,format="mp3")
        wav_path=file_path.replace(".mp3",".wav")
        audio.export(wav_path,format="wav")

        rate,data=wav.read(wav_path)

        if len(data.shape) >1:
            data=data.mean(axis=1)

        reduced_noise=nr.reduce_noise(y=data.astype(np.float32),sr=rate)

        reduced_noise=np.clip(reduced_noise,-1.0,1.0)

        reduced_wav=wav_path.replace(".wav","_reduced.wav")
        wav.write(reduced_wav,rate,(reduced_noise * 32767).astype(np.int16))


        reduced_mp3_path=file_path.replace(".mp3","_reduced.mp3")
        reduced_audio=AudioSegment.from_file(reduced_wav,format="wav")
        reduced_audio.export(reduced_mp3_path,format="mp3")

        os.remove(wav_path)
        os.remove(reduced_wav)

        return reduced_mp3_path

    except Exception as e:
        raise RuntimeError(f"Error during noise reduction: {str(e)}")
            