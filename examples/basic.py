from jseasy import Page


page = Page.from_html(
    """
    <main id="app"></main>
    <script>
      const item = document.createElement("h1");
      item.textContent = "Loaded without Chrome";
      document.querySelector("#app").appendChild(item);
    </script>
    """
)

print(page.select("#app h1").text)
