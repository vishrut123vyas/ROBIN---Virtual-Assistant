import speech_recognition as sr 
import webbrowser
import pyttsx3
import musicLibrary
import requests
from openai import OpenAI
from gtts import gTTS
from pydub import AudioSegment
import pygame
import os

recognizer=sr.Recognizer()
engine=pyttsx3.init()
newsapi="yourapikey"

def speak_old(text):
    engine.say(text)
    engine.runAndWait()


# def speak(text):
#     tts = gTTS(text)
#     tts.save('temp.mp3') 

#     # Initialize Pygame mixer
#     pygame.mixer.init()

#     # Load the MP3 file
#     pygame.mixer.music.load('temp.mp3')

#     # Play the MP3 file
#     pygame.mixer.music.play()

#     # Keep the program running until the music stops playing
#     while pygame.mixer.music.get_busy():
#         pygame.time.Clock().tick(10)
    
#     pygame.mixer.music.unload()
#     os.remove("temp.mp3") 

def speak(text):
    # Generate TTS MP3
    tts = gTTS(text)
    tts.save("temp.mp3")

    # Load and speed up using pydub
    sound = AudioSegment.from_file("temp.mp3")
    faster_sound = sound.speedup(playback_speed=1.3)  # Adjust speed factor as needed

    # Save the faster audio
    faster_sound.export("fast_temp.mp3", format="mp3")

    # Initialize Pygame mixer
    pygame.mixer.init()

    # Load and play the faster audio
    pygame.mixer.music.load("fast_temp.mp3")
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    # Cleanup
    pygame.mixer.music.unload()
    os.remove("temp.mp3")
    os.remove("fast_temp.mp3")





 

def aiProcess(command):
    client = OpenAI(api_key="<yourapikey>"
    )

    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a virtual assistant named robin skilled in general tasks like Alexa and Google Cloud. Give short responses please"},
        {"role": "user", "content": command}
    ]
    )

    return completion.choices[0].message.content





 

def processcommand(c):
     
     print(f"Processing command: {c}")

     if "open google" in c.lower():
        webbrowser.open("https://google.com")
     elif "open facebook" in c.lower():
        webbrowser.open("https://facebook.com")
     elif "open youtube" in c.lower():
        webbrowser.open("https://youtube.com")
     elif "open linkedin" in c.lower():
        webbrowser.open("https://linkedin.com")
     elif c.lower().startswith("play"):
        song = c.lower().split(" ")[1]
        link = musicLibrary.music[song]
        webbrowser.open(link)

     elif "mistake" in c.lower():
         speak("i am sorry , i will make it up to you")

         
     elif "news" in c.lower():
         r=requests.get(f"https://newsapi.org/v2/top-headlines?country=us&apiKey={newsapi}")
         if r.status_code == 200:
            # Parse the JSON response
            data = r.json()
            
            # Extract the articles
            articles = data.get('articles', [])
            
            # Print the headlines
            for article in articles:
                speak(article['title'])
      
     else:
        # Let OpenAI handle the request
            output = aiProcess(c)
            speak(output)


if __name__ == "__main__":
   speak("Initializing robin")

   while True:
            # listen to wake word lucius
            r = sr.Recognizer() 

            print("recognizing.........")

            
            try:

                with sr.Microphone() as source:
                    print("Listening...")
                    audio = r.listen(source, timeout=2, phrase_time_limit=1)
                word = r.recognize_google(audio)

                


                if(word.lower()=="robin"):
                    speak("hi batman")
                    # Listen for command
                    with sr.Microphone() as source:
                        speak("how can i assist you ")
                        print("hey batman , how can i assist you ")
                        audio = r.listen(source)
                        command = r.recognize_google(audio)

                        if command.lower()=="stop":
                         speak("goodbye batman")
                         break




                        processcommand(command)


            except Exception as e:
                print(" error; {0}".format(e))






