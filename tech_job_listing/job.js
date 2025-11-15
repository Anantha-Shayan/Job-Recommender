const express = require('express');
const router = express.Router();
const { LinkedInJobScraper } = require('linkedin-jobs-api');
const axios = require('axios');
const cheerio = require('cheerio');
 const { standardizeJob, isTechRole } = require('./job_filter.js');

// --- Naukri Scraping Helper ---
const NAUKRI_BASE_URL = 'https://www.naukri.com/';

async function scrapeNaukri(keyword, limit) {
    const jobs = [];
    const searchUrl = `${NAUKRI_BASE_URL}${keyword.toLowerCase().replace(/\s/g, '-')}-jobs`;
    
    try {
        const response = await axios.get(searchUrl, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        });
        const $ = cheerio.load(response.data);

        $('.jobTuple.bgWhite').slice(0, limit).each((i, element) => {
            const jobElement = $(element);
            
            const title = jobElement.find('.title.fw500').text().trim();
            const company = jobElement.find('.companyInfo.subTitle.ellipsis').text().trim();
            const location = jobElement.find('.location.locWdth').text().trim();
            const experience = jobElement.find('.experience').text().trim();
            const jobUrl = jobElement.find('.title.fw500').attr('href');

            const rawJob = {
                title,
                company,
                location,
                experience,
                source: 'Naukri',
                link: jobUrl ? jobUrl : searchUrl,
                description: 'N/A (Requires deep scraping)'
            };
            
            const standardized = standardizeJob(rawJob, 'naukri');

            if (isTechRole(standardized)) {
                jobs.push(standardized);
            }
        });

        return jobs;

    } catch (error) {
        console.error('Naukri Scraping Error:', error.message);
        throw new Error('Failed to scrape Naukri jobs.');
    }
}

// --- LinkedIn Scraping Helper ---
const linkedinScraper = new LinkedInJobScraper();

async function scrapeLinkedIn(params) {
    const { keyword, location, limit, experienceLevel, jobType, remoteFilter } = params;
    
    const apiParams = {
        keyword: keyword || 'Software Engineer',
        location: location || 'India',
        limit: parseInt(limit) || 10,
        experienceLevel: experienceLevel,
        jobType: jobType,
        remoteFilter: remoteFilter
    };

    try {
        const results = await linkedinScraper.run(apiParams);
        
        const filteredJobs = results
            .map(job => standardizeJob(job, 'linkedin'))
            .filter(isTechRole);

        return filteredJobs;

    } catch (error) {
        console.error('LinkedIn Scraping Error:', error.message);
        throw new Error('Failed to scrape LinkedIn jobs: ' + error.message);
    }
}


// --- Routes ---

router.get('/linkedin', async (req, res) => {
    try {
        const jobs = await scrapeLinkedIn(req.query);
        res.json({ source: 'LinkedIn', count: jobs.length, jobs });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

router.get('/naukri', async (req, res) => {
    try {
        const { keyword = 'tech', limit = 10 } = req.query;
        const jobs = await scrapeNaukri(keyword, parseInt(limit));
        res.json({ source: 'Naukri', count: jobs.length, jobs });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

router.get('/all', async (req, res) => {
    try {
        const { keyword = 'tech', limit = 10 } = req.query;
        const parsedLimit = parseInt(limit);

        const [linkedinJobs, naukriJobs] = await Promise.allSettled([
            scrapeLinkedIn({ ...req.query, limit: parsedLimit }),
            scrapeNaukri(keyword, parsedLimit)
        ]);

        const allJobs = [];
        const errors = [];

        if (linkedinJobs.status === 'fulfilled') {
            allJobs.push(...linkedinJobs.value);
        } else {
            errors.push({ source: 'LinkedIn', message: linkedinJobs.reason.message });
        }

        if (naukriJobs.status === 'fulfilled') {
            allJobs.push(...naukriJobs.value);
        } else {
            errors.push({ source: 'Naukri', message: naukriJobs.reason.message });
        }

        res.json({
            source: 'Combined',
            count: allJobs.length,
            jobs: allJobs,
            errors: errors.length > 0 ? errors : undefined
        });
    } catch (error) {
        res.status(500).json({ error: 'An unexpected error occurred during combined fetch: ' + error.message });
    }
});

module.exports = router;