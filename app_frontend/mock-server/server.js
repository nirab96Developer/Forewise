const express = require("express");
const cors = require("cors");
const fs = require("fs");
const path = require("path");

const app = express();
const PORT = 3001;

// Middleware
app.use(cors());
app.use(express.json({ limit: "10mb" }));
app.use(express.urlencoded({ extended: true }));

// Load mock data
const dataPath = path.join(__dirname, "data.json");
let mockData = {};

try {
  const data = fs.readFileSync(dataPath, "utf8");
  mockData = JSON.parse(data);
} catch (error) {
  console.error("Error loading mock data:", error);
  process.exit(1);
}

// Health check
app.get("/health", (req, res) => {
  res.json({ status: "OK", message: "Mock server is running" });
});

// Auth endpoints
app.post("/api/v1/auth/login", (req, res) => {
  console.log("Raw request body:", req.body);
  console.log("Request headers:", req.headers);
  console.log("Content-Type:", req.get("Content-Type"));

  try {
    const { username, password } = req.body;
    console.log("Parsed username:", username);
    console.log("Parsed password:", password);

    // Simple mock authentication
    const user = mockData.users.find((u) => u.username === username);

    if (user && (password === "admin" || password === "password")) {
      const token = `mock_token_${user.id}_${Date.now()}`;
      res.json({
        access_token: token,
        token_type: "bearer",
        user: {
          id: user.id,
          username: user.username,
          email: user.email,
          firstName: user.firstName,
          lastName: user.lastName,
          role: user.role,
        },
      });
    } else {
      res.status(401).json({ error: "Invalid credentials" });
    }
  } catch (error) {
    console.error("Error processing login request:", error);
    res.status(400).json({ error: "Invalid request format" });
  }
});

app.post("/api/v1/auth/logout", (req, res) => {
  res.json({ message: "Logged out successfully" });
});

app.get("/api/v1/auth/me", (req, res) => {
  // Mock user data
  res.json({
    id: "1",
    username: "admin",
    email: "admin@forewise.co",
    firstName: "מנהל",
    lastName: "מערכת",
    role: "admin",
  });
});

// Projects endpoints
app.get("/api/v1/projects/", (req, res) => {
  res.json(mockData.projects);
});

app.get("/api/v1/projects/:id", (req, res) => {
  const project = mockData.projects.find((p) => p.id === req.params.id);
  if (project) {
    res.json(project);
  } else {
    res.status(404).json({ error: "Project not found" });
  }
});

// Equipment endpoints
app.get("/api/v1/equipment/", (req, res) => {
  res.json(mockData.equipment);
});

app.get("/api/v1/equipment/:id", (req, res) => {
  const equipment = mockData.equipment.find((e) => e.id === req.params.id);
  if (equipment) {
    res.json(equipment);
  } else {
    res.status(404).json({ error: "Equipment not found" });
  }
});

// Users endpoints
app.get("/api/v1/users/", (req, res) => {
  res.json(mockData.users);
});

// Work logs endpoints
app.get("/api/v1/work_reports/", (req, res) => {
  res.json(mockData.workLogs);
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Mock server running on http://localhost:${PORT}`);
  console.log(`📊 Available endpoints:`);
  console.log(`   - GET  /health`);
  console.log(`   - POST /api/v1/auth/login`);
  console.log(`   - GET  /api/v1/projects/`);
  console.log(`   - GET  /api/v1/equipment/`);
  console.log(`   - GET  /api/v1/users/`);
  console.log(`   - GET  /api/v1/work_reports/`);
  console.log(`\n🔑 Test credentials:`);
  console.log(`   - Username: admin, Password: password`);
  console.log(`   - Username: manager, Password: password`);
  console.log(`   - Username: worker, Password: password`);
});
