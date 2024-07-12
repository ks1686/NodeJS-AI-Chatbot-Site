const express = require("express");
const session = require("express-session");
const bodyParser = require("body-parser");
const fs = require("fs");
const path = require("path");
const dotenv = require("dotenv");
const AwanLLM = require("./AwanLLM");
const crypto = require("crypto");

// Load environment variables
dotenv.config();

// Initialize Express
const app = express();
app.use(express.static(path.join(__dirname, "static")));
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "templates"));

// Middleware
app.use(bodyParser.urlencoded({ extended: true }));
app.use(
  session({
    secret: crypto.randomBytes(64).toString("hex"),
    resave: false,
    saveUninitialized: true,
  })
);

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

// Route to view the cart, transaction total, and hide_cart_button
app.get("/view_cart", (req, res) => {
  let total = 0;
  if (req.session.cart) {
    req.session.cart.forEach((item) => {
      total += item.price * item.quantity;
    });
  }

  res.render("view_cart.ejs", {
    cart: req.session.cart,
    total: total.toFixed(2),
    hide_cart_button: true,
  });
});

//Route to add item to the cart
app.post("/add_to_cart", (req, res) => {
  const { item_name, item_price, quantity } = req.body;

  if (!quantity || isNaN(quantity) || parseInt(quantity) < 1) {
    return res.status(400).send("Invalid quantity");
  }

  // Initialize the cart in the session if it doesn't exist
  if (!req.session.cart) {
    req.session.cart = [];
  }

  // Check if the item is already in the cart
  let itemFound = false;
  req.session.cart.forEach((item) => {
    if (item.name === item_name) {
      item.quantity += parseInt(quantity);
      itemFound = true;
    }
  });

  // If the item is not in the cart, add it
  if (!itemFound) {
    req.session.cart.push({
      name: item_name,
      price: parseFloat(item_price),
      quantity: parseInt(quantity),
    });
  }

  req.session.save((err) => {
    if (err) {
      console.error(err);
      return res.status(500).send("Failed to save the cart");
    }
  });

  // Stay on the same page
  res.redirect("back");
});

// Route to remove items from the cart
app.post("/remove_from_cart", (req, res) => {
  const { item_name } = req.body;

  if (!req.session.cart) {
    return res.status(400).send("Cart is empty");
  }

  req.session.cart = req.session.cart.filter((item) => item.name !== item_name);

  req.session.save((err) => {
    if (err) {
      console.error(err);
      return res.status(500).send("Failed to save the cart");
    }
  });

  // Stay on the same page
  res.redirect("back");
});

// Route to update item quantity inside the cart
app.post("/update_cart", (req, res) => {
  const { item_name, new_quantity } = req.body;

  if (!req.session.cart) {
    return res.status(400).send("Cart is empty");
  }

  if (!new_quantity || isNaN(new_quantity) || parseInt(new_quantity) < 1) {
    return res.status(400).send("Invalid quantity");
  }

  req.session.cart.forEach((item) => {
    if (item.name === item_name) {
      item.quantity = parseInt(new_quantity);
    }
  });

  req.session.save((err) => {
    if (err) {
      console.error(err);
      return res.status(500).send("Failed to save the cart");
    }

    // Stay on the same page
    res.redirect("back");
  });
});

// Route to handle chat requests
app.post("/chat", async (req, res) => {
  if (req.is("application/json")) {
    const { message } = req.body;

    // Add user message to the chat
    chatbot.role("user").content(message);
    const responses = await chatbot.sendChatCompletions();

    if (responses) {
      const joinedResponses = responses.join("");
      res.json({ chat_response: joinedResponses });
    } else {
      res.json({
        chat_response: "Sorry, there was an error processing your request.",
      });
    }
  } else {
    res.status(400).send("Invalid request type");
  }
});

// Start the server
const PORT = 8000;
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
  console.log(`Ngrok domain: https://noticeably-hardy-sunbird.ngrok-free.app`);
});
