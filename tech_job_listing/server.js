const express = require('express');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// CORS setup
app.use(cors({
    origin: '*',
    methods: ['GET'],
    allowedHeaders: ['Content-Type'],
}));

// Rate Limiting
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // Limit each IP to 100 requests per windowMs
    standardHeaders: true,
    legacyHeaders: false,
    message: 'Too many requests from this IP, please try again after 15 minutes',
});

app.use(limiter);
app.use(express.json());

// Import Job Routes (point to the actual filename `job.js`)
const jobRoutes = require('./job');

// Basic route
app.get('/', (req, res) => {
    res.status(200).json({
        message: 'Welcome to the Tech Job Listing API. Use /api/jobs/all to fetch listings.',
        endpoints: ['/api/jobs/linkedin', '/api/jobs/naukri', '/api/jobs/all']
    });
});

// Integrate Job Routes
app.use('/api/jobs', jobRoutes);

// Basic Error Handling
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({
        error: 'Internal Server Error',
        message: err.message
    });
});

// 404 Handler
app.use((req, res) => {
    res.status(404).json({
        error: 'Not Found',
        message: `Cannot GET ${req.originalUrl}`
    });
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});

module.exports = app;
