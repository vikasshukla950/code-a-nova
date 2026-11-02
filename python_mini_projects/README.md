# Python Mini Projects

Three beginner-to-intermediate Python projects.

## Setup
```bash
pip install -r requirements.txt     # file_organizer.py needs nothing extra
```
Requires Python 3.9+.

## 1. File Organizer (`file_organizer.py`) – Level 1(a)
Scans a folder, detects each file's type, and moves it into a category folder
(Images, Documents, Videos, Audio, Archives, Code, Installers, Others).
```bash
python file_organizer.py ~/Downloads --dry-run   # preview first!
python file_organizer.py ~/Downloads             # actually move files
```
- Name clashes are handled safely (`photo.jpg` -> `photo (1).jpg`)
- Hidden files and existing sub-folders are left alone
- Edit the `CATEGORIES` dictionary to add your own file types

## 2. URL Status Checker (`url_status_checker.py`) – Level 2(a)
Checks whether websites are up or down and shows status codes + response time.
```bash
python url_status_checker.py google.com github.com
python url_status_checker.py -f urls.txt
python url_status_checker.py            # interactive: type URLs, blank line to run
```
- Checks URLs in parallel; uses HEAD and falls back to GET if the server rejects HEAD
- Status < 400 = UP; 4xx/5xx, timeouts, DNS and SSL errors = DOWN
- Exit code `0` if all up, `2` if any down (handy for cron jobs / scripts)

## 3. Web Scraper (`web_scraper.py`) – Level 1(c)
Scrapes data with Requests + BeautifulSoup, follows pagination, saves CSV or JSON.
```bash
python web_scraper.py                              # quotes -> quotes.csv
python web_scraper.py --site books --format json   # books  -> books.json
python web_scraper.py --max-pages 3 --delay 2
```
- Targets practice sites built for scraping (quotes.toscrape.com, books.toscrape.com)
- To scrape a new site: write a `parse_*` function and add it to the `SITES` dict
- Always respect a site's robots.txt and terms of service
