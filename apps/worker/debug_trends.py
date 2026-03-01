import asyncio
from playwright.async_api import async_playwright

async def debug_google_trends():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        url = "https://trends.google.com/trending?geo=US"
        print(f"Going to: {url}")
        
        await page.goto(url, wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(5000)
        
        # Extract trends using specific patterns
        trends = await page.evaluate('''() => {
            const trends = [];
            const text = document.body.innerText;
            
            // Split by lines and find trend patterns
            const lines = text.split('\\n');
            
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i].trim();
                
                // Look for lines that are likely trend titles:
                // - Between 3-80 chars
                // - Not navigation items
                // - Not metadata (numbers, percentages, etc)
                if (line.length > 3 && line.length < 80) {
                    // Skip navigation and UI elements
                    if (['Trends', 'Home', 'Explore', 'Trending now', 'Sign in', 
                         'United States', 'Past 24 hours', 'All categories', 
                         'All trends', 'By relevance', 'Export', 'Search trends',
                         'Sort by title', 'Search volume', 'Started', 'Trend breakdown',
                         'Trend status'].includes(line)) {
                        continue;
                    }
                    
                    // Skip lines that are just numbers or percentages
                    if (/^\\d+[KM]?\\+?$/.test(line) || /^\\d+%$/.test(line)) {
                        continue;
                    }
                    
                    // Skip time indicators
                    if (/\\d+ hours? ago/.test(line) || /trending_up|arrow_upward|Active/.test(line)) {
                        continue;
                    }
                    
                    // Skip "more" indicators
                    if (/^\\+ \\d+ more$/.test(line)) {
                        continue;
                    }
                    
                    // This is likely a trend!
                    if (!line.startsWith('arrow_') && !line.includes('trending_')) {
                        trends.push(line);
                    }
                }
            }
            
            return [...new Set(trends)];
        }''')
        
        print(f"\nExtracted trends ({len(trends)}):")
        for i, trend in enumerate(trends[:20], 1):
            print(f"{i}. {trend}")
        
        await context.close()
        await browser.close()

asyncio.run(debug_google_trends())
