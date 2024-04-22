from moviepy.editor import VideoClip, TextClip, ImageClip, CompositeVideoClip, AudioFileClip
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
import matplotlib.pyplot as plt
import numpy as np
from gtts import gTTS
import shap
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

def get_shap_values(input_text):
    access_token = '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'
    tokenizer = AutoTokenizer.from_pretrained("gpt2", token = access_token)
    model = AutoModelForCausalLM.from_pretrained("gpt2", token = access_token)
    print('model loaded')
    # Set the device (CPU or GPU)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    # set model decoder to true
    model.config.is_decoder = True
    
    # set text-generation params under task_specific_params
    model.config.task_specific_params["text-generation"] = {
        "do_sample": True,
        "max_length": 50,
        "temperature": 0.7,
        "top_k": 50,
        "no_repeat_ngram_size": 2,
    }

    s = [input_text.lower()]
    explainer = shap.Explainer(model, tokenizer)
    shap_values = explainer(s)
    print('shap values generated')
    values = {}

    # Iterate over SHAP values and tokens
    for token_shap, token in zip(shap_values.values[0], tokenizer(s[0], return_tensors="pt")["input_ids"][0]):
        token_str = tokenizer.decode([token])
        values[token_str] = token_shap[-1]

    values = {key.strip(): value for key, value in values.items()}
    all_values = sorted(values.items(), key=lambda kv: (kv[0], kv[1]))
        
    # List of connecting words
    connect_words = [
        # Coordinating conjunctions
        'is','in','the','of','i','am','and', 'but', 'or', 'nor', 'for', 'yet', 'so',',','.','?','!',';','"','\\','(',')','[',']','{','}','on',
        # Subordinating conjunctions
        'after', 'although', 'as', 'because', 'before', 'if', 'since', 'so that',
        'though', 'unless', 'until', 'when', 'whenever', 'while','what',
        # Correlative conjunctions
        'either', 'neither', 'both', 'not','only','also', 'whether',
        # Conjunctive adverbs
        'however', 'moreover', 'nevertheless', 'therefore', 'consequently', 'accordingly',
        'furthermore', 'otherwise', 'meanwhile', 'nonetheless',
        # Prepositions
        'with', 'without', 'by', 'through', 'among', 'between', 'beside', 'near', 'after',
        'before', 'during'
    ]

    # Remove elements from all_values that are present in connect_words
    filtered_values = [(k, v) for k, v in all_values if k not in connect_words]
    all_values = filtered_values
    print('filtered values')
    positive = []

    for x in all_values:
        if x[1] > 0:
            positive.append(x)
        else:
            positive.append((x[0],x[1]*-1))
    sz_p = 5 if len(positive) >= 5 else len(positive)
    
    if len(positive) > 0:
        positive = sorted(positive, key=lambda x: x[1], reverse=True)
        return positive[0:sz_p]

def generate_video(input_text):
    # Get the positive words and their SHAP values
    positive_words = get_shap_values(input_text)
    print('positive words generated')
    # Create a white background clip
    background_clip = ImageClip("media/white_background.png", duration=10)

    # Create a pie chart clip
    labels = [word for word, value in positive_words]
    values = [value for word, value in positive_words]
    total_positive_impact = sum(values)
    percentages = [value / total_positive_impact * 100 for value in values]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(values, labels=labels, autopct='%1.1f%%')
    ax.axis('equal')

    def make_frame(t):
        fig.canvas.draw()
        rgb_array = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        return rgb_array.reshape(fig.canvas.get_width_height()[::-1] + (3,))

    pie_chart_clip = VideoClip(make_frame, duration=10)
    pie_chart_clip = pie_chart_clip.set_position(("left", "top"))

    # Create a text clip for the input text
    text_clip = TextClip(input_text, fontsize=30, color='black').set_duration(10)

    # Create a dynamic explanation text
    positive_word_contributions = ",\n ".join([f"'{word}' ({percentage:.1f}%)" for word, percentage in zip(labels, percentages)])

    explanation_text = f"Based on the input '{input_text},' \nthe model output is influenced positively by the words \n{positive_word_contributions}."
    if len(positive_words) == 3:
        text = f"\nso the the word '{positive_words[0][0]}' and '{positive_words[1][0]}'\n and '{positive_words[2][0]}' are the major reason to get the output."
    elif len(positive_words) == 2:
        text = f"\nso the the word '{positive_words[0][0]}', '{positive_words[1][0]}'\n  are the major reason to get the output."
    else:
        text = f"\nso the the word '{positive_words[0][0]}' is the major reason to get the output."
    explanation_text = explanation_text + text
    explanation_clip = TextClip(explanation_text, fontsize=45, color='black', bg_color='white', size=(1500, 1000)).set_position(('right', 'top')).set_duration(10)


    # Generate audio from explanation text using gTTS
    tts = gTTS(text=explanation_text, lang='en')
    tts.save("media/explanation_audio.mp3")
    print('audio generated')

    # Load the audio clip
    audio_clip = AudioFileClip("media/explanation_audio.mp3")

    video_with_new_audio = pie_chart_clip.set_audio(audio_clip)

    # Combine all clips
    final_clip = CompositeVideoClip([background_clip, video_with_new_audio, text_clip, explanation_clip,])

    # Set the fps of the final clip
    final_clip.fps = 24

    # Write the final video
    final_clip.write_videofile("media/output_video.mp4")
    print('video generated')