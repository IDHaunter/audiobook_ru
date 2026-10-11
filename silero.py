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
    text="1. Утопия. Лето 2037-го выдалось чертовски жарким, но тут, в зале «Скворец», под потолок набитом вычислительным оборудованием, температура редко превышала 27 градусов. Довольно комфортно, если бы не этот постоянный звук, который Дэниел Раск слышал даже во сне. Шестьдесят герц. Ровный, глубокий, лишённый всякого выражения гул — так гудят двадцать тысяч вентиляторов, работающих в идеальном согласии друг с другом. Первые годы этот звук вызывал у него тошноту. Потом он к нему привык.",
    speaker='kseniya',
    sample_rate=48000
)

# Сохранение в WAV
import soundfile as sf
sf.write('output.wav', audio.numpy(), 48000)