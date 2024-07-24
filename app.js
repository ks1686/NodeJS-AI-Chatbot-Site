const express = require("express");
const session = require("express-session");
const multer = require("multer");
const path = require("path");
const fs = require("fs");
const dotenv = require("dotenv");
const crypto = require("crypto");
const bodyParser = require("body-parser");
const AwanLLM = require("./AwanLLM");
const gtts = require("gtts");
const { exec } = require("child_process");
const uuid = require("uuid");
const axios = require("axios");
/* Custom Depay module that doesn't seem to work
const { verify } = require("@depay/js-verify-signature"); 
*/

// Load environment variables
dotenv.config();

// Initialize Express
const app = express();
app.use(express.static(path.join(__dirname, "static")));
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "templates"));

// Middleware
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());
app.use(
  session({
    secret: crypto.randomBytes(64).toString("hex"),
    resave: false,
    saveUninitialized: true,
  })
);

// Middleware to clear cart if menu parameter changes
app.use((req, res, next) => {
  const newMenuParam = req.query.menu;
  const oldMenuParam = req.session.menuParam;

  // Clear cart if the menu parameter has changed
  if (newMenuParam && oldMenuParam && newMenuParam !== oldMenuParam) {
    req.session.cart = [];
  }

  // Update session with the current menu parameter
  req.session.menuParam = newMenuParam;

  next();
});

// Set up storage for multer with a static filename
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, "uploads/");
  },
  filename: (req, file, cb) => {
    cb(null, "recording.mp3");
  },
});

// Initialize upload and create audio directory
const upload = multer({ storage: storage });
const audioDirectory = path.join(__dirname, "static", "audio");
if (!fs.existsSync("uploads")) {
  fs.mkdirSync("uploads");
}
if (!fs.existsSync(audioDirectory)) {
  fs.mkdirSync(audioDirectory);
}

// Declare chatbot variables
let chatbot;

// All needed environment variables for Depay (keys from pem file)
const integrationId = process.env.DEPAY_INTEGRATION_ID.toString();
const privateKey = fs.readFileSync("keys/private_key.pem");
const public_key = fs.readFileSync("keys/depay_public_key.pem");

// Function to verify request and get response signature from Depay
const verifyDepayRequest = async (req) => {
  const signature = req.headers["x-signature"].toString();
  const data = req.body;
  console.log("Request signature: ", signature);
  console.log("Request body: ", data);

  /* Custom module that doesn't work, Depay docs (https://github.com/DePayFi/js-verify-RSA-PSS-SHA256#functionoality)
  // let verified = await verify({
  //   signature: req.headers["x-signature"],
  //   data: JSON.stringify(data),
  //   public_key,
  // });
  */

  const verify = crypto.createVerify("RSA-SHA256");
  verify.update(JSON.stringify(data));
  verify.verify(public_key, req.headers["x-signature"], "base64");

  if (!verify) {
    // Log an Express error for Depay request verification failed
    console.error("Depay request verification failed");
  }

  return verify;
};

const getDepayResponseSignature = (responseString) => {
  const signature = crypto.sign("sha256", Buffer.from(responseString), {
    key: privateKey,
    padding: crypto.constants.RSA_PKCS1_PSS_PADDING,
    saltLength: 64,
  });

  const urlSafeBase64Signature = signature
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");

  return urlSafeBase64Signature;
};

// Function to load menu data based on parameter
function loadMenuData(menuParam) {
  let menuData = [];
  let menuText = "";

  const menuFileName = menuParam ? `${menuParam}.json` : "menu.json";
  try {
    const data = fs.readFileSync(menuFileName, "utf8");
    menuData = JSON.parse(data).data;

    // Generate formatted menu text
    menuText = menuData
      .filter((item) => item.in_stock)
      .map(
        (item) =>
          `${item.item}: $${item.price.toFixed(2)} - ${item.description}`
      )
      .join("\n");
  } catch (err) {
    console.error(`Error loading menu file: ${menuFileName}`, err);
    process.exit(1);
  }

  return { menuData, menuText };
}

// Route to load the main page
app.get("/", (req, res) => {
  const menuParam = req.query.menu;
  const { menuData, menuText } = loadMenuData(menuParam);

  // Initialize LLM Chat Client
  const LLM_API_KEY = process.env.AWANLLM_API_KEY;
  const LLM_MODEL = process.env.MODEL_NAME;
  if (!LLM_API_KEY || !LLM_MODEL) {
    console.error("No API key or model name found.");
    process.exit(1);
  }
  chatbot = new AwanLLM(LLM_API_KEY, LLM_MODEL);
  chatbot.role("system").content("Here is our menu:\n" + menuText);

  res.render("index.ejs", {
    title: "Main Page", // Set the title for index.ejs
    hide_cart_button: false, // Adjust based on your logic
    menuData, // Pass the menu data to index.ejs
  });
});

// Route to serve the menu data
app.get("/menu", (req, res) => {
  const menuParam = req.query.menu;
  const { menuData } = loadMenuData(menuParam);
  res.json(menuData.filter((item) => item.in_stock));
});

// Route to handle category selection
app.get("/category/:category_name", (req, res) => {
  const menuParam = req.query.menu;
  const { menuData } = loadMenuData(menuParam);
  const category_name = req.params.category_name;
  const items_in_category = menuData.filter(
    (item) => item.category === category_name && item.in_stock
  );
  res.render("category_items.ejs", {
    category_name: category_name,
    items: items_in_category,
    menuParam: menuParam || "menu", // Pass the menu parameter to the template
  });
});

// Route to view the cart, transaction total, and hide_cart_button
app.get("/view_cart", (req, res) => {
  const menuParam = req.query.menu;
  const guid = uuid.v4();

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
    menuParam: menuParam || "menu", // Pass the menu parameter to the template
    integrationId: integrationId,
    guid: guid,
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
    const message = req.body.message;

    // Add user message to the chat
    chatbot.role("user").content(message);
    let responses = await chatbot.sendChatCompletions();

    if (responses) {
      // Remove all newline characters from the responses
      responses = responses.replace(/\n/g, "");

      res.json({ chat_response: responses });
    } else {
      res.json({
        chat_response: "Sorry, there was an error processing your request.",
      });
    }
  } else {
    res.status(400).send("Invalid request type");
  }
});

// Route to handle text-to-speech requests
app.post("/tts", async (req, res) => {
  if (req.is("application/json")) {
    const text = req.body.text;

    try {
      // Generate audio file using gtts
      const gttsObject = new gtts(text, "en");
      const audioFilePath = path.join(
        __dirname,
        "static",
        "audio",
        "output.mp3"
      ); // Adjust the path as needed
      gttsObject.save(audioFilePath, async (err, result) => {
        if (err) {
          console.error("Error saving audio:", err);
          return res.status(500).json({ error: "Failed to generate audio" });
        }

        // Serve the audio file URL back to the client
        const audioUrl = `/audio/output.mp3`;
        res.json({ audio_url: audioUrl });
      });
    } catch (error) {
      console.error("Error:", error);
      res.status(500).send("Failed to process the text-to-speech request");
    }
  } else {
    res.status(400).send("Invalid request type");
  }
});

// Route to handle audio recording
app.post("/record", upload.single("audio"), (req, res) => {
  try {
    // The audio file is saved as "uploads/recording.mp3"
    const filePath = req.file.path;

    // Run CLI Whisper commands
    exec(`whisper -otxt -f txt ${filePath}`, (error, stdout, stderr) => {
      if (error) {
        console.error("Error processing audio:", error);
        return res.status(500).send("Failed to process the audio");
      }

      // Process the output text (located in /txt/recording.txt)
      const processedText = fs.readFileSync(
        path.join(__dirname, "txt", "recording.txt"),
        "utf8"
      );

      // Delete the audio file
      fs.unlink(filePath, (err) => {
        if (err) {
          console.error("Error deleting audio file:", err);
        }
      });

      // Respond with success and processed text
      res.json({ message: "Audio recorded successfully", text: processedText });
    });
  } catch (error) {
    console.error("Error:", error);
    res.status(500).send("Failed to process the audio");
  }
});

// Route to handle the payment process
app.post("/process_payment", async (req, res) => {
  // Get the total amount from the request body
  const total = req.body.total;

  // Pull the GUID from the request body
  const guid = req.body.guid;

  const paymentGatewayUrl = process.env.PAYMENT_GATEWAY_URL;

  const paymentData = {
    Version: "1.0",
    MerchantId: process.env.MERCHANT_ID,
    TerminalId: process.env.TERMINAL_ID,
    Identification: process.env.IDENTIFICATION,
    UniqueId: guid,
    TenderType: "2",
    TransactionType: "1",
    SaleAmount: total,
    Timeout: "-1",
  };

  try {
    // Make POST request to payment gateway
    const response = await axios.post(paymentGatewayUrl, paymentData);

    // Check if the payment was successful
    if (response.data.TransactionResult === "APPROVED") {
      const cardNum = response.data.CardNumber;
      const authAmount = response.data.AuthorizedAmount;

      // Clear the cart
      req.session.cart = [];

      // Save the session
      req.session.save((err) => {
        if (err) {
          console.error(err);
          return res.status(500).send("Failed to save the cart");
        }
      });

      // Send JSON response with payment details
      res.json({
        success: true,
        message: "Payment successful",
        cardNum: cardNum,
        authAmount: authAmount,
      });
    } else {
      // Payment failed
      res.status(400).json({
        success: false,
        message: "Payment failed",
      });
    }
  } catch (error) {
    console.error("Error processing payment:", error);
    res.status(500).json({
      success: false,
      message: "Failed to process the payment",
    });
  }
});

// Payment endpoint for the cryptocurrency payment to communicate to
app.post("/depay/endpoint", async (req, res) => {
  if (!(await verifyDepayRequest(req))) {
    return res.status(400).send("Unauthorized request");
  }

  const configuration = {
    amount: {
      currency: "USD",
      fix: req.body.total,
    },
    accept: [
      {
        blockchain: "ethereum",
        token: "0xdac17f958d2ee523a2206206994597c13d831ec7",
        receiver: "0x4e260bB2b25EC6F3A59B478fCDe5eD5B8D783B02",
      },
      {
        blockchain: "ethereum",
        token: "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        receiver: "0x4e260bB2b25EC6F3A59B478fCDe5eD5B8D783B02",
      },
    ],
  };

  res.setHeader(
    "x-signature",
    getDepayResponseSignature(JSON.stringify(configuration))
  );
  res.status(200).json(configuration);
});

// Start the server
const PORT = 8000;
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
  console.log(`Ngrok domain: https://noticeably-hardy-sunbird.ngrok-free.app`);
});
