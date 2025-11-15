const TECH_KEYWORDS = [
    'software', 'developer', 'engineer', 'data', 'devops', 'frontend', 'backend', 'fullstack', 'cloud', 
    'architect', 'security', 'machine learning', 'ai', 'data science','system','network', 'react', 
    'angular', 'python', 'nodejs', 'ops', 'aws', 'azure', 'docker', 'kubernetes', 'sql', 'nosql', 
    'linux', 'unix','javascript', 'python', 'java', 'c++', 'golang', 'rust', 'kotlin', 'typescript'
];

const standardizeJob = (job, source) => {
    if (source === 'linkedin') {
        return {
            id: job.jobId,
            title: job.title,
            company: job.company,
            location: job.location,
            description: job.description,
            link: job.link,
            postedDate: job.postedDate,
            source: 'LinkedIn',
            experienceLevel: job.experienceLevel || 'N/A',
            jobType: job.jobType || 'N/A'
        };
    } else if (source === 'naukri') {
        return {
            id: job.id || 'N/A',
            title: job.title || 'N/A',
            company: job.company || 'N/A',
            location: job.location || 'N/A',
            description: job.description || 'N/A',
            link: job.link || 'N/A',
            postedDate: job.postedDate || 'N/A',
            source: 'Naukri',
            experienceLevel: job.experience || 'N/A',
            jobType: job.jobType || 'N/A'
        };
    }
    return job;
};

const isTechRole = (job) => {
    const text = `${job.title} ${job.description}`.toLowerCase();
    return TECH_KEYWORDS.some(keyword => text.includes(keyword));
};

module.exports = {
    standardizeJob,
    isTechRole,
    TECH_KEYWORDS
};