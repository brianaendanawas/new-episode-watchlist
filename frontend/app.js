document.addEventListener("DOMContentLoaded", () => {
  const episodesList = document.getElementById("episodes");
  const loadBtn = document.getElementById("loadBtn");
  const searchBox = document.getElementById("searchBox");
  const lastUpdated = document.getElementById("lastUpdated");

  let allEpisodes = [];

  // Show last updated
  if (lastUpdated) {
    lastUpdated.textContent = new Date().toLocaleString();
  }

  // Load episodes from API Gateway
  loadBtn.addEventListener("click", () => {
    fetch("https://8c7523bn7g.execute-api.us-east-1.amazonaws.com/episodes?showId=show1")
      .then(res => res.json())
      .then(data => {
        allEpisodes = data; // Save full list
        renderList(allEpisodes);
      })
      .catch(err => {
        episodesList.innerHTML = `<li style="color:red;">Error: ${err}</li>`;
      });
  });

  // Search filter
  searchBox.addEventListener("input", () => {
    const query = searchBox.value.toLowerCase();
    const filtered = allEpisodes.filter(ep =>
      ep.title.toLowerCase().includes(query)
    );
    renderList(filtered);
  });

  // Render helper
  function renderList(items) {
    episodesList.innerHTML = "";
    items.forEach(ep => {
      const li = document.createElement("li");
      li.textContent = ep.title + (ep.isNew ? " ⭐" : "");
      episodesList.appendChild(li);
    });
  }
});
