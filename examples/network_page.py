from jseasy import Page


with Page.open("https://example.com") as page:
    print(page.select("h1").text)
    print("HTML bytes:", len(page.html()))
