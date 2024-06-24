import openai

# Set your OpenAI API key
openai.api_key = "sk-proj-d6XVLyi1kgt3aooG8xd2T3BlbkFJEI3AnHtXTyodpxF2BQaX"


def chatbot():
    # Create a list to store all the messages for context
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
    ]

    # Keep repeating the following
    while True:
        # Prompt user for input
        message = input("User: ")

        # Exit program if user inputs "quit"
        if message.lower() == "quit":
            break

        # Add each new message to the list
        messages.append({"role": "user", "content": message})

        # Request gpt-3.5-turbo for chat completion
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=messages
        )

        # Print the response and add it to the messages list
        chat_message = response["choices"][0]["message"]["content"]
        print(f"Bot: {chat_message}")
        messages.append({"role": "assistant", "content": chat_message})


if __name__ == "__main__":
    print("Start chatting with the bot (type 'quit' to stop)!")
    chatbot()
