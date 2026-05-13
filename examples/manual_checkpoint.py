from jseasy import Page


def has_security_challenge(page: Page) -> bool:
    text = page.eval("() => document.documentElement.textContent")
    markers = ["captcha", "security challenge", "sicherheitsabfrage"]
    return any(marker in text.lower() for marker in markers)


with Page.open("https://example.com") as page:
    if has_security_challenge(page):
        print("Manual checkpoint required. Open the URL in a browser and solve it manually.")
        print(page.url)
    else:
        print(page.html())
