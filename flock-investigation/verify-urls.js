/**
 * verify-urls.js
 * Uses Playwright + Firefox in headless mode with stealth settings
 * to verify 3 URLs that returned 403 to automated tools.
 */
const { firefox } = require('playwright');

const URLS = [
  {
    url: 'https://transparency.flocksafety.com/',
    label: 'Flock Safety Transparency Portal',
    checks: [
      'Is this a working transparency portal?',
      'Search for "Fountain Valley" - does Fountain Valley CA PD have a portal?',
      'Confirm these cities have portals: Costa Mesa, Buena Park, Newport Beach, Westminster',
    ],
  },
  {
    url: 'https://www.cnbc.com/2026/02/12/amazons-ring-cancels-flock-partnership-amid-super-bowl-ad-backlash.html',
    label: 'CNBC - Amazon Ring cancels Flock partnership',
    checks: [
      'Verify claim: "Amazon Ring cancels planned Flock integration"',
      'Was the partnership "planned" (never active) vs already active?',
    ],
  },
  {
    url: 'https://santacruzlocal.org/2025/11/07/ice-accessed-capitola-license-plate-data-police-say-it-was-a-mistake/',
    label: 'Santa Cruz Local - ICE accessed Capitola plate data',
    checks: [
      'Verify claim: "Capitola PD admits ICE accessed their plate data (a mistake)"',
      'Does this article mention the Oakland PD lawsuit?',
    ],
  },
];

(async () => {
  console.log('=== Playwright Firefox Stealth URL Verification ===\n');

  const browser = await firefox.launch({
    headless: true,
    firefoxUserPrefs: {
      // Stealth: disable webdriver flag
      'dom.webdriver.enabled': false,
      // Stealth: standard user-agent behavior
      'general.useragent.override': '',
      // Disable telemetry
      'toolkit.telemetry.enabled': false,
      // Allow JS
      'javascript.enabled': true,
    },
  });

  const context = await browser.newContext({
    userAgent:
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0',
    locale: 'en-US',
    timezoneId: 'America/Los_Angeles',
    viewport: { width: 1920, height: 1080 },
    // Extra stealth headers
    extraHTTPHeaders: {
      'Accept-Language': 'en-US,en;q=0.9',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
      'Sec-Fetch-Dest': 'document',
      'Sec-Fetch-Mode': 'navigate',
      'Sec-Fetch-Site': 'none',
      'Sec-Fetch-User': '?1',
      'Upgrade-Insecure-Requests': '1',
    },
  });

  for (const entry of URLS) {
    console.log('─'.repeat(78));
    console.log(`URL: ${entry.url}`);
    console.log(`Label: ${entry.label}`);
    console.log('─'.repeat(78));

    const page = await context.newPage();

    try {
      const response = await page.goto(entry.url, {
        waitUntil: 'domcontentloaded',
        timeout: 30000,
      });

      const status = response ? response.status() : 'no response';
      console.log(`HTTP Status: ${status}`);

      // Wait a bit for JS rendering
      await page.waitForTimeout(3000);

      const title = await page.title();
      console.log(`Page Title: "${title}"`);

      // Extract visible text content from body
      const bodyText = await page.evaluate(() => {
        // Remove script/style elements
        const clone = document.body.cloneNode(true);
        clone.querySelectorAll('script, style, noscript, svg, img').forEach(el => el.remove());
        return clone.innerText || clone.textContent || '';
      });

      // Clean up whitespace
      const cleanText = bodyText.replace(/\n{3,}/g, '\n\n').trim();

      console.log(`\nPage text length: ${cleanText.length} chars`);

      // URL-specific checks
      if (entry.url.includes('transparency.flocksafety.com')) {
        console.log('\n--- TRANSPARENCY PORTAL CHECKS ---');

        // Check if it's a working portal
        const isPortal = cleanText.toLowerCase().includes('transparency') ||
                         cleanText.toLowerCase().includes('flock') ||
                         title.toLowerCase().includes('transparency');
        console.log(`Working transparency portal: ${isPortal ? 'YES' : 'NO / UNCLEAR'}`);

        // Check for specific cities
        const cities = ['Fountain Valley', 'Costa Mesa', 'Buena Park', 'Newport Beach', 'Westminster'];
        for (const city of cities) {
          const found = cleanText.includes(city) || cleanText.toLowerCase().includes(city.toLowerCase());
          console.log(`  "${city}" found on page: ${found ? 'YES' : 'NO'}`);
        }

        // Try searching if there's a search box
        try {
          const searchInput = await page.$('input[type="search"], input[type="text"], input[placeholder*="search" i], input[placeholder*="Search" i]');
          if (searchInput) {
            console.log('\nFound search input - searching for "Fountain Valley"...');
            await searchInput.fill('Fountain Valley');
            await page.waitForTimeout(2000);
            const afterSearchText = await page.evaluate(() => document.body.innerText);
            const fvFound = afterSearchText.toLowerCase().includes('fountain valley');
            console.log(`  "Fountain Valley" in search results: ${fvFound ? 'YES' : 'NO'}`);
          } else {
            console.log('\nNo search input found on page.');
          }
        } catch (e) {
          console.log(`Search attempt error: ${e.message}`);
        }

        // Print first 3000 chars for inspection
        console.log('\n--- PAGE TEXT (first 3000 chars) ---');
        console.log(cleanText.substring(0, 3000));
      }

      if (entry.url.includes('cnbc.com')) {
        console.log('\n--- CNBC ARTICLE CHECKS ---');

        const mentionsCancels = cleanText.toLowerCase().includes('cancel');
        const mentionsPlanned = cleanText.toLowerCase().includes('planned');
        const mentionsActive = cleanText.toLowerCase().includes('already active') ||
                               cleanText.toLowerCase().includes('existing partnership') ||
                               cleanText.toLowerCase().includes('active partnership');
        const mentionsIntegration = cleanText.toLowerCase().includes('integration');
        const mentionsRing = cleanText.toLowerCase().includes('ring');
        const mentionsFlock = cleanText.toLowerCase().includes('flock');
        const mentionsSuperBowl = cleanText.toLowerCase().includes('super bowl');

        console.log(`  Mentions "cancel": ${mentionsCancels}`);
        console.log(`  Mentions "planned": ${mentionsPlanned}`);
        console.log(`  Mentions "already active"/"existing partnership": ${mentionsActive}`);
        console.log(`  Mentions "integration": ${mentionsIntegration}`);
        console.log(`  Mentions "Ring": ${mentionsRing}`);
        console.log(`  Mentions "Flock": ${mentionsFlock}`);
        console.log(`  Mentions "Super Bowl": ${mentionsSuperBowl}`);

        // Print first 5000 chars for inspection
        console.log('\n--- ARTICLE TEXT (first 5000 chars) ---');
        console.log(cleanText.substring(0, 5000));
      }

      if (entry.url.includes('santacruzlocal.org')) {
        console.log('\n--- SANTA CRUZ LOCAL ARTICLE CHECKS ---');

        const mentionsCapitola = cleanText.toLowerCase().includes('capitola');
        const mentionsICE = cleanText.includes('ICE') || cleanText.toLowerCase().includes('immigration and customs');
        const mentionsMistake = cleanText.toLowerCase().includes('mistake');
        const mentionsLicensePlate = cleanText.toLowerCase().includes('license plate');
        const mentionsOakland = cleanText.toLowerCase().includes('oakland');
        const mentionsLawsuit = cleanText.toLowerCase().includes('lawsuit');
        const mentionsFlock = cleanText.toLowerCase().includes('flock');

        console.log(`  Mentions "Capitola": ${mentionsCapitola}`);
        console.log(`  Mentions "ICE" or "Immigration and Customs": ${mentionsICE}`);
        console.log(`  Mentions "mistake": ${mentionsMistake}`);
        console.log(`  Mentions "license plate": ${mentionsLicensePlate}`);
        console.log(`  Mentions "Oakland": ${mentionsOakland}`);
        console.log(`  Mentions "lawsuit": ${mentionsLawsuit}`);
        console.log(`  Mentions "Flock": ${mentionsFlock}`);

        // Print first 5000 chars for inspection
        console.log('\n--- ARTICLE TEXT (first 5000 chars) ---');
        console.log(cleanText.substring(0, 5000));
      }

    } catch (err) {
      console.log(`ERROR loading page: ${err.message}`);
    }

    await page.close();
    console.log('\n');
  }

  await browser.close();
  console.log('=== Verification Complete ===');
})();
