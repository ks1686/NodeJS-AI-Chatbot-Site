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
