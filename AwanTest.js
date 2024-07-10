const AwanLLM = require("./AwanLLM");
const dotenv = require("dotenv");

dotenv.config();

AWANLLM_API_KEY = process.env.AWANLLM_API_KEY;
AWANLLM_MODEL = process.env.MODEL_NAME;

async function run() {
  const chatbot = new AwanLLM(AWANLLM_API_KEY, AWANLLM_MODEL);

  chatbot
    .role("system")
    .content("You are a helpful assistant.")
    .role("user")
    .content("Hello!")
    .role("assistant")
    .content("Hi!, how can I help you today?");

  const responses = await chatbot.sendChatCompletions();
  if (responses) {
    const joinedResponses = responses.join("");
    console.log("Bot", joinedResponses);
  }
}

run();
