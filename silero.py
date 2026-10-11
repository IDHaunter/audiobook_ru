import ssl

ssl._create_default_https_context = ssl._create_unverified_context

import torch

device = torch.device('cpu')
model, example_text = torch.hub.load(
    repo_or_dir='snakers4/silero-models',
    model='silero_tts',
    language='ru',
    speaker='v4_ru'
)
model.to(device)

# Voice variants: 'aidar', 'baya', 'kseniya', 'xenia', 'eugene'
audio = model.apply_tts(
    text="Дэниел смотрел объявление в баре «Пеликан» — последнем баре в Литтл-Форке, где ещё продавали настоящий алкоголь людям с напечатанной печенью. На экране президент произносила слова «величайшее достижение в истории нашего вида», и голос у неё срывался — это не было игрой.",
    speaker='kseniya',
    sample_rate=48000
)

# Сохранение в WAV
import soundfile as sf
sf.write('output.wav', audio.numpy(), 48000)