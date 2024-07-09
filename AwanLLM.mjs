import fetch from "node-fetch";
import dotenv from "dotenv";

dotenv.config();

const AWANLLM_API_KEY = process.env.AWANLLM_API_KEY;

async function sendChatCompletions() {
  const url = "https://api.awanllm.com/v1/chat/completions";

  const payload = {
    model: "Awanllm-Llama-3-8B-Dolfin",
    messages: [
      { role: "system", content: "You are a helpful assistant." },
      { role: "user", content: "Hello!" },
      { role: "assistant", content: "Hi!, how can I help you today?" },
    ],
    repetition_penalty: 1.1,
    temperature: 0.7,
    top_p: 0.9,
    top_k: 40,
    max_tokens: 1024,
    stream: true,
  };

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${AWANLLM_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const responseText = await response.text();

    const regex = /{"content":"(.*?)"/g;
    let match;

    const botResponses = [];

    while ((match = regex.exec(responseText)) !== null) {
      botResponses.push(match[1]);
    }

    return botResponses;
  } catch (error) {
    console.error("Error sending chat completions:", error.message);
    return null;
  }
}

// Example of assigning botResponses to a variable
async function processChat() {
  try {
    const botResponses = await sendChatCompletions();
    if (botResponses) {
      // join all of the array responses
      const joinedResponses = botResponses.join("");
      console.log("Joined Responses:", joinedResponses);
    }
  } catch (error) {
    console.error("Error processing chat:", error);
  }
}

processChat();
