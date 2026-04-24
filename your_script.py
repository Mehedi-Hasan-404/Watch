import asyncio
from playwright.async_api import async_playwright

async def scrape_streams():
    base_url = "https://livecricketsl.cc.nf/events/"
    found_media = set()

    async with async_playwright() as p:
        # Launch with necessary arguments for GitHub Actions
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()

        # Listener to catch the actual media manifest URLs from background traffic
        page.on("request", lambda req: found_media.add(req.url) 
                if (".m3u8" in req.url or ".mpd" in req.url) else None)

        print(f"[*] Accessing main events page...")
        await page.goto(base_url, wait_until="networkidle")

        # 1. Get all event/stream page URLs (the ones with the IDs)
        # We look for links that likely lead to the player pages
        stream_pages = await page.eval_on_selector_all(
            "a[href*='id='], a[href*='/watch/'], a[href*='/event/']", 
            "nodes => nodes.map(n => n.href)"
        )
        
        unique_pages = list(set(stream_pages))
        print(f"[*] Found {len(unique_pages)} stream ID pages.")

        # 2. Visit each ID page to extract the deep-link m3u8/mpd
        for stream_url in unique_pages:
            print(f"[*] Deep-scraping ID page: {stream_url}")
            try:
                # Navigate to the specific ID page
                await page.goto(stream_url, wait_until="domcontentloaded", timeout=30000)
                
                # Some sites require a 'Play' or 'Watch' click to trigger the manifest load
                play_button = page.locator("button, .play-btn, #player").first
                if await play_button.is_visible():
                    await play_button.click(force=True)
                
                # Give the player 8 seconds to resolve the manifest handshake
                await asyncio.sleep(8) 
            except Exception as e:
                print(f"[!] Skip {stream_url}: {e}")

        await browser.close()

    # 3. Create the M3U Playlist
    if found_media:
        with open("live.m3u", "w") as f:
            f.write("#EXTM3U\n")
            # Filter out common false positives (like ad-trackers with .m3u8 in name)
            clean_links = [l for l in found_media if "chunklist" not in l]
            for i, link in enumerate(sorted(clean_links)):
                f.write(f"#EXTINF:-1, Live Stream {i+1}\n")
                f.write(f"{link}\n")
        print(f"[!] Created live.m3u with {len(clean_links)} links.")
    else:
        print("[X] No m3u8/mpd found. Ensure matches are currently LIVE.")

if __name__ == "__main__":
    asyncio.run(scrape_streams())
