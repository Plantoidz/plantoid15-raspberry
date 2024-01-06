import sys
filename = sys.argv[1]
import speech_recognition as sr


if __name__ == "__main__":


    with sr.AudioFile(filename) as source:

        r = sr.Recognizer()
#        r.energy_threshold = 50
#        r.dynamic_energy_threshold = False
        r.adjust_for_ambient_noise(source=source)

        audio = r.record(source)
        usertext = "";

        try:
            print("trying to recognize from ... " + filename)
            usertext = r.recognize_google(audio, language ='en-US', show_all=True)

        except Exception as e:
            print("Exception: " + str(e))

        except sr.UnknownValueError as e:
            print("Google Speech Recognition could not understand audio: ", e)

        except sr.RequestError as e:
            print("Could not request results from Google Speech Recognition service; {0}".format(e))

        print(usertext)
