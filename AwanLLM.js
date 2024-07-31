const dotenv = require("dotenv");

dotenv.config();

// AwanLLM class
class AwanLLM {
  // Constructor
  constructor(
    apiKey = process.env.AWANLLM_API_KEY,
    model = "Awanllm-Llama-3-8B-Dolfin",
  ) {
    this.apiKey = apiKey;
    this.model = model;
    this.messages = [];
    this.config = {
      repetition_penalty: 1.1,
      temperature: 0.7,
      top_p: 0.9,
      top_k: 40,
      max_tokens: 1024,
      stream: true,
    };
  }

  // Set the role
  role(role) {
    this.currentRole = role;
    return this;
  }

  // Add content
  content(content) {
    if (!this.currentRole) {
      throw new Error("Role must be set before content.");
    }
    this.messages.push({ role: this.currentRole, content: content });
    this.currentRole = null; // Reset the current role
    return this;
  }

  // Send the chat completions to the AwanLLM API
  async sendChatCompletions() {
    const fetch = (await import("node-fetch")).default;
    const url = "https://api.awanllm.com/v1/chat/completions";

    const payload = {
      model: this.model,
      messages: this.messages,
      ...this.config,
    };

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      // Parse the response
      const responseText = await response.text();
      const regex = /{"content":"(.*?)"/g;
      let match;
      let botResponses = [];

      // Extract the bot responses from the response
      while ((match = regex.exec(responseText)) !== null) {
        botResponses.push(match[1]);
      }
      if (botResponses.length === 0) {
        throw new Error("No bot responses found in the response");
      }

      // Join the bot responses
      if (botResponses) {
        botResponses = botResponses.join("");

        // Remove all newline characters
        botResponses = botResponses.replace(/\n/g, "");
        botResponses = botResponses.replace(/\n\n/g, "");
        return botResponses;
      } else {
        throw new Error("No bot responses found in the response");
      }
    } catch (error) {
      console.error("Error sending chat completions:", error.message);
      return null;
    }
  }
}

// Export the AwanLLM class
module.exports = AwanLLM;
