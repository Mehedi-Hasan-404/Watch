import asyncio
from playwright.async_api import async_playwright

async def scrape_streams():
    url = "https://livecricketsl.cc.nf/events/"
    found_media = []

    async with async_playwright() as p:
        # Launch with no-sandbox for GitHub Actions compatibility
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context()
        page = await context.new_page()

        # Intercept m3u8/mpd requests
        page.on("request", lambda req: found_media.append(req.url) 
                if (".m3u8" in req.url or ".mpd" in req.url) and req.url not in found_media else None)

        print(f"[*] Accessing: {url}")
        await page.goto(url, wait_until="networkidle")

        # Find the active 'Watch Now' button for the MI vs CSK match
        try:
            # Locate the button based on the current site's structure
            watch_button = page.locator("text='Watch Now'").first
            if await watch_button.is_visible():
                print("[*] Match is LIVE. Clicking Watch button to trigger manifest...")
                await watch_button.click()
                # Wait for the player to negotiate the handshake and fetch the m3u8
                await asyncio.sleep(10) 
        except Exception as e:
            print(f"[!] Stream button not found or already loaded: {e}")

        await browser.close()

    print("\n--- Extracted Stream Links ---")
    if found_media:
        for link in found_media:
            print(link)
    else:
        print("No active streams captured. Ensure the match hasn't gone to a break.")

if __name__ == "__main__":
    asyncio.run(scrape_streams())
