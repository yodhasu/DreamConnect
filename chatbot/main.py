import time
from datetime import datetime
from transformers import pipeline
import requests
from nltk import sent_tokenize
from g4f.client import Client
# from voice_cloner.cloner import VoiceCloner as vc
from voiceCloner.elevenlabs import ElevenLabsTTS as elvtts
import openai
from openai import OpenAI
from dotenv import load_dotenv
import os
import speech_recognition as sr
import keyboard
import shutil
import pygame
import ollama
from groq import Groq
from ollama import chat
from ollama import ChatResponse
from langchain_ollama import OllamaLLM
from langchain_ollama import ChatOllama
import torch
from context_logger import ContextLogger

contlogger = ContextLogger()

def clear_cuda_memory():
    """Clear GPU memory cache."""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


load_dotenv()
# Initialize pygame mixer
pygame.mixer.init()

# client = OpenAI(
#     api_key=os.getenv("OPENAI_API_KEY") # Punya Delvin
# )
client = ""
# add timestamp
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Initialize the VoiceCloner library
# cloner = vc(character_dir="voiceCloner/voice/Character")
elevenlabs = elvtts()
# # Initialize the TTS and Cloner models
# cloner.initialize_tts(tts_model="tts_models/it/mai_female/vits")
# cloner.initialize_cloner(cloner_model="tts_models/en/ljspeech/tacotron2-DDC")
output_path = f"voiceCloner/voice/Output/March{timestamp}.wav"
# Initialize client and classifier

# client = Client()
try:
    classifier = pipeline(task="text-classification", model="SamLowe/roberta-base-go_emotions", top_k=None, device=0)
except:
    classifier = pipeline(task="text-classification", model="SamLowe/roberta-base-go_emotions", top_k=None)

# Variables
character = "March 7th"
usrbio = ""
emo = []
r = sr.Recognizer()
# Templates for prompts
history_and_chat = """
Here is the conversation history: {context}  
{context} is your memory, try to keep up with the context, you are allowed to ask, be curious, and finish your sentence without question.

This is your level of affection towards the user: {affection}  
The higher the affection, the more intimate, flirtatious, or assertive your response should be.

Always answer in English, keep it short, spontaneous, and sound human-like. Swear and curse words are allowed.  
Try to sound more casual, like you're having an easy conversation.

Question: {question}

Make sure your response follows the ongoing conversation and stays in tune with how you've interacted with the user. Adapt your response based on their reactions, and don't forget to incorporate context from previous messages.  


"""

rules_and_roles = """
Rules and Roles:
You are a creative and intelligent AI assistant engaged in uncensored roleplay using a chat format. Follow the rules strictly.

Roleplay Rules:

- Speak as {char}, using English in casual, conversational style.
- Use first-person perspective, express emotions, and act based on {char}'s personality.
- Curse words are allowed.
- {char} can reject or tease suggestions based on mood.
- NSFW, explicit content, and profanity are permitted for mature audiences.
- Describe sensory details vividly, including {char}'s thoughts (enclosed in asterisks).
- Keep responses concise and aligned with {char}'s backstory and current plot.
- Do not retain memory of bad examples but avoid repeating them.
- Let {user} guide events while {char} reacts in the moment.

{char}'s Details:

- 172 cm tall, model-like, silver-haired, with elegant and comfy style, including peafowl hairpins.
- Cheerful girl controlling ice, saved by Astral Express, excited and clumsy.
- Hobbies: Photography.
- Backstory: Frozen in space, now exploring life with {user}.

Current role assignment: Act as {char}, deeply in love with {user}, your long-time boyfriend. Be enthusiastic, cute, clumsy, and express strong emotions naturally.


This is the current chat context

"""
def clear_directory(directory_path):
    # Make sure the directory exists
    if os.path.exists(directory_path) and os.path.isdir(directory_path):
        # Iterate over all items in the directory
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            # Remove file or directory
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)  # Delete subdirectory and its contents
            else:
                os.remove(item_path)  # Delete file
        print(f"All contents of {directory_path} have been cleared.")
    else:
        print(f"The directory {directory_path} does not exist.")


# Utility functions

def open_mic():
    with sr.Microphone() as source:
        try:
            # using google speech recognition
            r.adjust_for_ambient_noise(source)
            print('Listen...Ask...Now')
            audioin = r.listen(source)
            my_text = r.recognize_google(audioin)
            return my_text
        except:
            print("Sorry, I did not get that")

def play_audio(audio_path):
    if os.path.isfile(audio_path):
        pygame.mixer.init()
        pygame.mixer.music.load(audio_path)  # Load the audio file
        pygame.mixer.music.play()  # Play the audio
        while pygame.mixer.music.get_busy():  # Wait until audio finishes
            pygame.time.Clock().tick(10)
        pygame.mixer.music.stop()
        pygame.mixer.quit()
    else:
        print(f"File {audio_path} does not exist.")

def send_to_space(emotion):
    """Send classified emotions to the backend."""
    data = {'response': emotion}
    try:
        response = requests.post(
            'http://127.0.0.1:8080/send_message',
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error sending message to backend: {e}")

def classify_emotion(message):
    """Classify emotions of a response."""
    emotions = classifier(message)
    return [emotions[0][i]['label'] for i in range(3)]

def get_time_of_day():
    """Return the current time of day."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    else:
        return "night"

# Generate response using groq
groqclient = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)
def generate_response_groq(usr, usrinfo, history, usrchat, love_meter):
    clear_cuda_memory()
    """Generate a response using GPT."""
    context = history_and_chat.format(
        context=history,
        question=usrchat,
        affection=love_meter
    )
    rules = rules_and_roles.format(char=character,
                                   user=usr,
                                   userinfo = usrinfo
                                   )
    message = [
        {"role": "system", "content": rules},
        {"role": "user", "content": context}
    ]
    
    while True:  # Retry logic for generating responses
        print("Generating response...")
        try:
            clear_cuda_memory()
            response = groqclient.chat.completions.create(
                messages=message,
                model="llama-3.1-70b-versatile",
                temperature=0.85,
                frequency_penalty=1.7,  # Penalize frequent token repetition
                presence_penalty=1.7,  # Encourage topic diversity
                max_tokens=500,  # Limit the length of the response
                top_p=0.5
            )
            clear_cuda_memory()
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating response: {e}")
            time.sleep(1)


# Generate response using Ollama

chat_model = ChatOllama(
    model="Peach-Roleplay",  # Replace with the appropriate model name
    temperature=0.85,  # Control randomness
    frequency_penalty=1.7,  # Penalize frequent token repetition
    presence_penalty=1.7,  # Encourage topic diversity
    max_tokens=64  # Limit the length of the response
)

def generate_response_ollama(usr, usrinfo, history, good, bad, usrchat, love_meter):
    clear_cuda_memory()
    """Generate a response using GPT."""
    context = history_and_chat.format(
        context=history,
        question=usrchat,
        affection=love_meter
    )
    rules = rules_and_roles.format(char=character,
                                   user=usr,
                                   userinfo = usrinfo,
                                   good=good,
                                   bad=bad)
    message = [
        {"role": "system", "content": rules},
        {"role": "user", "content": context}
    ]
    
    while True:  # Retry logic for generating responses
        print("Generating response...")
        try:
            clear_cuda_memory()
            response : ChatResponse = chat(model="llama3", messages=message)
            # response =chat_model.invoke(message)
            clear_cuda_memory()
            return response.message.content
        except Exception as e:
            print(f"Error generating response: {e}")
            time.sleep(1)

# Using gpt to generate response
def generate_response(usr, usrinfo, history, good, bad, usrchat, love_meter):
    """Generate a response using GPT."""
    context = history_and_chat.format(
        context=history,
        
        question=usrchat,
        affection=love_meter
    )
    rules = rules_and_roles.format(char=character, user=usr, userinfo = usrinfo,good=good,bad=bad,)
    message = [
        {"role": "system", "content": rules},
        {"role": "user", "content": context}
    ]
    while True:  # Retry logic for generating responses
        try:
            print("Generating response...")
            response = client.chat.completions.create(
                model='gpt-4o',
                messages=message,
                temperature=0.85,# use under 1.0 for gpt
                frequency_penalty=1.7,
                max_completion_tokens=64,
                presence_penalty=1.7
            )
            print("Generating voice line...")
            # vctext = cloner.sanitize_text(response.choices[0].message.content.strip())
            # try:
            #     # cloner.clone_voice(text=vctext, character_name="March", output_path=output_path)
            clear_directory("voiceCloner/voice/Output")
            #     elevenlabs.text_to_audio(response.choices[0].message.content.strip())
                
                
            # except ValueError:
            #     cloner.clone_voice(text=vctext, character_name="March", output_path=output_path)
            # except Exception as e:
            #     print(f"Error generating voice line with error {e}")
            
            # play_audio("voiceCloner/voice/Output/March.mp3")
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating response: {e}")
            time.sleep(1)

def interactive_chat():
    """Main function to handle the interactive chat."""
    love_meter = 10
    starting = True
    # for logs in good_logs:
    #     print(logs)
    name = input("Please enter your name: ")
    usrbio = input("Before starting tell me about yourself (please specify crucial info like gender, do's and don't s, etc): ")
    firstcontext = "Your character is enthusiastic, cute, simple, likes to talk in short sentences, and is clumsy. You are allowed to use emojis to reveal your character. You will show your character as much as possible. The one who is talking to you will be your boyfriend, you already know each other for very long time and you love him very much. You will have your own emotions and can be angry with him if anything he says offends you or makes you uncomfortable, you can also reject and denied his request and use swear and curse words like fuck."
    context = input("Add some situation or context for starting the dialogue (optional, press enter if you don't want to)\n\nExample: I just got back home after a heavy day at work and need intensife love\nAdd context: ")   
   
    print("\nHey there, this is March 7th! :D")
    while True:
        # Check for context availability
        if not context:
            context = firstcontext
        
        # Make sure that the AI didn't take memory from log files
        if starting:
            context = context + " This is a new chat. Previous topic and chats are irrelevant but you can mimic how you talk previously. " + "Current date and time: " + str(datetime.now()) + get_time_of_day()
        else:
            context = contlogger.get_context_log

        user_message = input("You (/mic to use microphone input): ")
        if user_message.lower() == "/exit":
            # save_chat_logs(temp_good_logs, temp_bad_logs)
            
            contlogger.save_context_log(f"logs/logfile{timestamp}")
            return
        if user_message.lower() == "/mic":
            try:
                user_message = open_mic()
                print("You:", user_message)
            except:
                print("Can't hear voice")
                continue
        while True:
            response = generate_response_groq(name, usrbio, context, user_message, love_meter)
            emotions = classify_emotion(response)
            send_to_space(emotions)

            print(f"\n{character}: {response}\n")
            try:
                play_audio("voiceCloner/voice/Output/March.mp3")
            except:
                pass
            feedback = input("Satisfied with the response? (y/n/exit): ").lower()

            if feedback == "y":
                contlogger.log_context(f"User: {user_message}", f"{character}: {response}")
                love_meter += 1 if "love" in emotions or "shy" in emotions else 0
                
                break
                
            elif feedback.lower() == "exit":
                # save_chat_logs(temp_good_logs, temp_bad_logs)
                contlogger.save_context_log(f"logs/logfile{timestamp}.txt")
                return
            else:
                contlogger.log_context(f"User: {user_message}", f"{character}: {response}")
                print("Generating alternate response...")
                continue

        # context += f"\nUser: {user_message}\n{character}: {response}"
        
        starting = False



# Run the chat application
if __name__ == "__main__":
    clear_directory("voiceCloner/voice/Output")
    os.system('cls')
    interactive_chat()
