import datetime as dt
import text2speech as t2s
def wish():
    dt_now = dt.datetime.now()
    hour = dt_now.hour
    if hour < 12:
        return "Good Morning!"
    elif 12 <= hour < 18:
        return "Good Afternoon!"
    else:
        return "Good Evening!"
while True:
    if t2s.textfromt2s == "No Transcription Available":
        print("No Transcription Available")
    else:
        print(t2s.textfromt2s)