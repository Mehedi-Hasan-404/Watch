import asyncio
import os
from playwright.async_api import async_playwright

async def scrape_streams():
    url = "https://livecricketsl.cc.nf/events/"
    found_media = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context()
        page = await context.new_page()

        # Catch media links
        page.on("request", lambda req: found_media.append(req.url) 
                if (".m3u8" in req.url or ".mpd" in req.url) and req.url not in found_media else None)

        print(f"[*] Loading {url}...")
        await page.goto(url, wait_until="networkidle")

        # Try to trigger the player if a 'Watch' button exists
        try:
            watch_btn = page.locator("text='Watch Now'").first
            if await watch_btn.is_visible():
                await watch_btn.click()
                await asyncio.sleep(10) # Wait for stream to negotiate
        except:
            pass

        await browser.close()

    # Create/Update the M3U file
    if found_media:
        with open("live.m3u", "w") as f:
            f.write("#EXTM3U\n")
            for i, link in enumerate(found_media):
                f.write(f"#EXTINF:-1, Cricket Stream {i+1}\n")
                f.write(f"{link}\n")
        print(f"[!] Success: Created live.m3u with {len(found_media)} links.")
    else:
        print("[X] No streams found.")

if __name__ == "__main__":
    asyncio.run(scrape_streams())
