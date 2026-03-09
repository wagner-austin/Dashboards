/**
 * Deep checks for the articles that need more context.
 */
const { firefox } = require('playwright');

(async () => {
  const browser = await firefox.launch({
    headless: true,
    firefoxUserPrefs: {
      'dom.webdriver.enabled': false,
    },
  });

  const context = await browser.newContext({
    userAgent:
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0',
    locale: 'en-US',
    timezoneId: 'America/Los_Angeles',
    viewport: { width: 1920, height: 1080 },
    extraHTTPHeaders: {
      'Accept-Language': 'en-US,en;q=0.9',
    },
  });

  // === 1. Flock Transparency Portal - try alternate URL patterns ===
  console.log('=== CHECK 1: Flock Transparency Portal ===\n');

  const flockUrls = [
    'https://transparency.flocksafety.com/',
    'https://transparency.flocksafety.com/fountain-valley-ca-police-department',
    'https://transparency.flocksafety.com/costa-mesa-ca-police-department',
    'https://www.flocksafety.com/transparency',
    'https://www.flocksafety.com/transparency-hub',
  ];

  for (const url of flockUrls) {
    const page = await context.newPage();
    try {
      const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
      const status = response ? response.status() : 'none';
      const title = await page.title();
      await page.waitForTimeout(2000);

      let textSnippet = '';
      try {
        textSnippet = await page.evaluate(() => {
          if (!document.body) return '(no body)';
          const clone = document.body.cloneNode(true);
          clone.querySelectorAll('script, style, noscript, svg').forEach(el => el.remove());
          return (clone.innerText || '').substring(0, 1000);
        });
      } catch(e) {
        textSnippet = '(eval failed)';
      }

      console.log(`${url}`);
      console.log(`  Status: ${status} | Title: "${title}"`);
      console.log(`  Text preview: ${textSnippet.substring(0, 300)}`);
      console.log();
    } catch (err) {
      console.log(`${url}`);
      console.log(`  ERROR: ${err.message}\n`);
    }
    await page.close();
  }

  // === 2. CNBC - get more article text (the "planned" vs "active" question) ===
  console.log('\n=== CHECK 2: CNBC - "planned" vs "active" partnership detail ===\n');

  const cnbcPage = await context.newPage();
  try {
    await cnbcPage.goto(
      'https://www.cnbc.com/2026/02/12/amazons-ring-cancels-flock-partnership-amid-super-bowl-ad-backlash.html',
      { waitUntil: 'domcontentloaded', timeout: 30000 }
    );
    await cnbcPage.waitForTimeout(3000);

    const fullText = await cnbcPage.evaluate(() => {
      const clone = document.body.cloneNode(true);
      clone.querySelectorAll('script, style, noscript, svg, img, nav, header, footer').forEach(el => el.remove());
      return (clone.innerText || '').replace(/\n{3,}/g, '\n\n').trim();
    });

    // Search for key phrases about planned vs active
    const lines = fullText.split('\n');
    const keyPhrases = ['planned', 'integration', 'announced', 'partnership', 'october', 'option to share', 'active'];
    const relevantLines = lines.filter(line => {
      const lower = line.toLowerCase();
      return keyPhrases.some(p => lower.includes(p)) && line.trim().length > 20;
    });

    console.log('Relevant lines about planned/active status:');
    relevantLines.forEach(l => console.log(`  > ${l.trim()}`));

    // Print full article body (chars 2000-8000 to skip nav)
    console.log('\n--- FULL ARTICLE BODY (chars 2000-8000) ---');
    console.log(fullText.substring(2000, 8000));
  } catch (err) {
    console.log(`ERROR: ${err.message}`);
  }
  await cnbcPage.close();

  // === 3. Santa Cruz Local - search full text for Oakland ===
  console.log('\n=== CHECK 3: Santa Cruz Local - Oakland/lawsuit search ===\n');

  const scPage = await context.newPage();
  try {
    await scPage.goto(
      'https://santacruzlocal.org/2025/11/07/ice-accessed-capitola-license-plate-data-police-say-it-was-a-mistake/',
      { waitUntil: 'domcontentloaded', timeout: 30000 }
    );
    await scPage.waitForTimeout(3000);

    const fullText = await scPage.evaluate(() => {
      const clone = document.body.cloneNode(true);
      clone.querySelectorAll('script, style, noscript, svg, img').forEach(el => el.remove());
      return (clone.innerText || '').replace(/\n{3,}/g, '\n\n').trim();
    });

    console.log(`Full text length: ${fullText.length} chars`);

    // Search for Oakland
    const oaklandIdx = fullText.toLowerCase().indexOf('oakland');
    if (oaklandIdx >= 0) {
      console.log(`\n"Oakland" FOUND at char ${oaklandIdx}:`);
      console.log(`  Context: "...${fullText.substring(Math.max(0, oaklandIdx - 100), oaklandIdx + 200)}..."`);
    } else {
      console.log('\n"Oakland" NOT found anywhere in full article text.');
    }

    // Search for lawsuit
    const lawsuitIdx = fullText.toLowerCase().indexOf('lawsuit');
    if (lawsuitIdx >= 0) {
      console.log(`\n"lawsuit" FOUND at char ${lawsuitIdx}:`);
      console.log(`  Context: "...${fullText.substring(Math.max(0, lawsuitIdx - 200), lawsuitIdx + 300)}..."`);
    } else {
      console.log('\n"lawsuit" NOT found in article.');
    }

    // Print article body (chars 3000-10000 for the main content)
    console.log('\n--- ARTICLE BODY (chars 3000-10000) ---');
    console.log(fullText.substring(3000, 10000));
  } catch (err) {
    console.log(`ERROR: ${err.message}`);
  }
  await scPage.close();

  await browser.close();
  console.log('\n=== Deep Verification Complete ===');
})();
