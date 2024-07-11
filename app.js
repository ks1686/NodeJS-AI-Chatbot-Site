const express = require("express");
const fs = require("fs");
const path = require("path");
const dotenv = require("dotenv");
const AwanLLM = require("./AwanLLM");
const { Leopard } = require("@picovoice/leopard-node");

// Load environment variables
dotenv.config();

// Initialize Express
const app = express();
app.use(express.static(path.join(__dirname, "static")));
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "templates"));

// Load the menu data from JSON
let menuData = [];
let menuText = ""; // Declare the variable outside try-catch to access later

try {
  const data = fs.readFileSync("menu.json", "utf8");
  menuData = JSON.parse(data).data;

  // Generate formatted menu text
  menuText = menuData
    .filter((item) => item.in_stock)
    .map(
      (item) => `${item.item}: $${item.price.toFixed(2)} - ${item.description}`
    )
    .join("\n");
} catch (err) {
  console.error(err);
  process.exit(1);
}

// Initialize LLM Chat Client
const LLM_API_KEY = process.env.AWANLLM_API_KEY;
const LLM_MODEL = process.env.MODEL_NAME;
if (!LLM_API_KEY || !LLM_MODEL) {
  console.error("No API key or model name found.");
  process.exit(1);
}
const chatbot = new AwanLLM(LLM_API_KEY, LLM_MODEL);
chatbot.role("system").content("Here is our menu:\n" + menuText);

// Initialize Leopard
const leopard = new Leopard(process.env.PICOVOICE_ACCESS_KEY);

// Route to load the main page
app.get("/", (req, res) => {
  res.render("index.ejs", {
    title: "Main Page", // Set the title for index.ejs
    hide_cart_button: false, // Adjust based on your logic
    // You can pass additional data to index.ejs here if needed
  });
});

// Route to handle category selection
app.get("/category/:category_name", (req, res) => {
  const category_name = req.params.category_name;
  const items_in_category = menuData.filter(
    (item) => item.category === category_name && item.in_stock
  );
  res.render("category_items.ejs", {
    category_name: category_name,
    items: items_in_category,
  });
});

// Start the server
const PORT = 8000;
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
  console.log(`Ngrok domain: https://noticeably-hardy-sunbird.ngrok-free.app`);
});
