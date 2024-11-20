# import torch
# import TTS
# import os
# from TTS.api import TTS

# device = "cuda" if torch.cuda.is_available() else "cpu"

# chardir = "voice/Character/"
# char = "March"
# lang = "en"
# charvoice = f"{char}_{lang}.wav"
# ref_clips = ""
# for voice in os.listdir(chardir):
#     print(voice)
#     if voice == charvoice:
#         ref_clips = chardir + voice

# ref_clips

# # List available 🐸TTS models
# mode_list = TTS().list_models()

# # download all model
# # for model in mode_list:
# #     TTS(model).to(device)

# # Init TTS
# tts = TTS("tts_models/it/mai_female/vits").to(device)

# # cloner tts
# model = "voice_conversion_models/multilingual/vctk/freevc24"
# text = "This is a text to test voice cloning capability of the current model"
# charvoice = "voice/Character/VO_JA_Archive_March_7th_1.wav"
# # cloner = TTS("tts_models/en/ljspeech/tacotron2-DDC", progress_bar=True).to(device)

# cloner = TTS("tts_models/en/ljspeech/tacotron2-DDC", progress_bar=True).to(device)
# cloner.tts_with_vc_to_file(text=text, speaker_wav = ref_clips, file_path= "voice/Output/March1.wav")


from elevenlabs import stream, voices, play, save, Voice
from elevenlabs.client import ElevenLabs
import time
import os
from dotenv import load_dotenv

load_dotenv()

try:
  client = ElevenLabs(
     api_key=os.getenv('ELEVENLABS_API_KEY')
  )
except TypeError:
  exit("Ooops! You forgot to set ELEVENLABS_API_KEY in your environment!")

# CALLING voices() IS NECESSARY TO INSTANTIATE 11LABS FOR SOME FUCKING REASON
all_voices = client.voices.get_all()
print(f"\nAll ElevenLabs voices: \n{all_voices.voices}\n")



# Convert text to speech, then save. Return file directory.
def text_to_audio(input_text, save_as_wave=True, subdirectory="voice/Output"):
    audio_saved = client.generate(
        text=input_text,
        voice="March 7th",
        model="eleven_multilingual_v2"
    )
    if save_as_wave:
        file_name = f"___Msg{str(hash(input_text))}.wav"
    else:
        file_name = f"___Msg{str(hash(input_text))}.mp3"
    tts_file = os.path.join(os.path.abspath(os.curdir), subdirectory, file_name)
    save(audio_saved,tts_file)
    return tts_file

# Convert text to speech, then play it out loud
def text_to_audio_played(self, input_text, voice):
    audio = client.generate(
        text=input_text,
        voice=voice,
        model="eleven_turbo_v2_5"
    )
    play(audio)