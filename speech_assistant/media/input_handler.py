from speech_to_text import listen

def get_input():

    typed = input("Command (press ENTER for voice): ").strip()

    if typed:
        return typed.lower()

    print("Listening...")

    voice = listen()

    if voice:
        print("Voice:", voice)
        return voice.lower()

    return ""