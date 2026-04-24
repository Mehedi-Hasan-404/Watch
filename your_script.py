import asyncio
from playwright.async_api import async_playwright

async def scrape_streams():
    url = "https://livecricketsl.cc.nf/events/"
    found_media = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = await browser.new_context()
        page = await context.new_page()

        # Monitor all network traffic for stream manifests
        page.on("request", lambda req: found_media.add(req.url) 
                if (".m3u8" in req.url or ".mpd" in req.url) else None)

        print(f"[*] Navigating to {url}...")
        await page.goto(url, wait_until="networkidle")

        # 1. Look for all 'Watch' or 'Channel' buttons
        # This selector targets common patterns on these types of sites
        buttons = page.locator("button:has-text('Watch'), .channel-link, a:has-text('Channel')")
        count = await buttons.count()
        print(f"[*] Found {count} potential stream triggers.")

        for i in range(count):
            try:
                print(f"[*] Triggering stream {i+1}...")
                await buttons.nth(i).click()
                # Wait briefly for the player to initialize the specific manifest
                await asyncio.sleep(4) 
            except:
                continue

        await browser.close()

    # Save all unique findings to the M3U file
    if found_media:
        with open("live.m3u", "w") as f:
            f.write("#EXTM3U\n")
            for i, link in enumerate(sorted(found_media)):
                f.write(f"#EXTINF:-1, Cricket Stream {i+1}\n")
                f.write(f"{link}\n")
        print(f"[!] Success: live.m3u created with {len(found_media)} unique links.")
    else:
        print("[X] No streams captured. The match may not be live yet.")

if __name__ == "__main__":
    asyncio.run(scrape_streams())
