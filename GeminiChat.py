import google.generativeai as genai
import os

genai.configure(api_key="AIzaSyAgmkGK-aer9goZ3L3G9F63uEWoiM-7zN8")

model = genai.GenerativeModel("gemini-1.5-flash")

# prompt the user to start chatting
print("Start chatting with the bot (type 'quit' to stop)!")
while True:
    # get user input
    message = input("User: ")

    # exit the program if the user types "quit"
    if message.lower() == "quit":
        break

    # generate a response from the model
    response = model.generate_content(message)

    # print the response
    print(f"Bot: {response.text}")
