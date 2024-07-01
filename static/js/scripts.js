let mediaRecorder;
let chunks = [];

function startRecording() {
  navigator.mediaDevices
    .getUserMedia({ audio: true })
    .then(function (stream) {
      mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.ondataavailable = function (e) {
        chunks.push(e.data);
      };
      mediaRecorder.onstop = function () {
        const blob = new Blob(chunks, { type: mediaRecorder.mimeType });
        chunks = [];

        // Append user message to chat box
        appendMessage("User", "Audio message");

        // send the audio to the server
        const formData = new FormData();
        formData.append("audio", blob, "output.mp3");

        fetch("/record", {
          method: "POST",
          body: formData,
        })
          .then((response) => response.json())
          .then((data) => {
            console.log("Success:", data);
          })
          .catch((error) => {
            console.error("Error:", error);
          });
      };

      mediaRecorder.start();
      document.getElementById("recordBtn").style.display = "none"; // Hide record button
      document.getElementById("stopBtn").style.display = "inline-block"; // Show stop button
    })
    .catch(function (err) {
      console.error("Error accessing microphone:", err);
    });
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
    document.getElementById("stopBtn").style.display = "none"; // Hide stop button
    document.getElementById("recordBtn").style.display = "inline-block"; // Show record button
  }
}

function toggleRecording() {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    stopRecording();
  } else {
    startRecording();
  }
}

// Event listener for the record button
document.getElementById("recordBtn").addEventListener("click", function () {
  startRecording();
});

// Function to handle whether the input is a number
function isNumber(event) {
  const charCode =
    typeof event.which === "number" ? event.which : event.keyCode;
  const char = String.fromCharCode(charCode);
  return /^\d$/.test(char);
}

// Function to handle the keydown event
function standardKeyHandler(field, event) {
  const allowedKeys = [
    "Backspace",
    "Delete",
    "ArrowLeft",
    "ArrowRight",
    "Tab",
    "PageUp",
    "PageDown",
    "Home",
    "End",
  ];

  // get the key, supporting older browsers
  const key = event.key || String.fromCharCode(event.keyCode);

  if (key === "Enter" || key === "Escape") {
    field.blur();
    return true;
  }

  return (
    allowedKeys.includes(key) || event.ctrlKey || event.metaKey || event.altKey
  );
}

function handleNumericPaste(event) {
  let clipboardData = event.clipboardData || window.clipboardData;

  if (clipboardData) {
    let pastedData = clipboardData.getData("text/plain");
    if (/\D/.test(pastedData)) {
      event.preventDefault();
      return false; // Prevent the paste
    }
  }
  return true; // Allow the paste if clipboardData is unavailable or if it's numeric
}

// Refill the text box with the default value if it's empty
function refillTextBox(textBox) {
  if (textBox.value.trim() === "") textBox.value = textBox.defaultValue;
}

// Clear the text box if it contains the default value
function clearTextBox(textBox) {
  if (textBox.value.trim() === textBox.defaultValue) textBox.value = "";
}

async function sendMessage() {
  const chatInput = document.getElementById("chat-input");
  const message = chatInput.value;
  if (message.trim() === "") return;

  // Append user message to chat box
  appendMessage("User", message);
  chatInput.value = "";

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      throw new Error("Network response was not ok");
    }

    const data = await response.json();
    // Extract bot message from response, where format is { "chat_response": "message" }
    const botMessage = data.chat_response;

    // Append bot response to chat box
    appendMessage("Bot", botMessage);
  } catch (error) {
    console.error("Error:", error);
    appendMessage("Bot", "Sorry, there was an error processing your request.");
  }
}

function appendMessage(sender, message) {
  const chatBox = document.getElementById("chat-box");
  const messageElement = document.createElement("div");
  messageElement.className = "message";
  messageElement.innerHTML = `<strong>${sender}:</strong> ${message}`;
  chatBox.appendChild(messageElement);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function toggleChat() {
  var chatContainer = document.getElementById("chat-container");
  var toggleBtn = document.getElementById("toggle-chat-btn");

  chatContainer.classList.toggle("collapsed");

  if (chatContainer.classList.contains("collapsed")) {
    toggleBtn.textContent = "+";
  } else {
    toggleBtn.textContent = "-";
  }
}

function quickSubmitChat(event) {
  if (event.key === "Enter") {
    sendMessage();
  }
}
