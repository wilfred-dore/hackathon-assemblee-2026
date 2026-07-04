// Client API du Rapporteur — version « backend » (serveur FastAPI).
// La version statique (GitHub Pages) réimplémente ces mêmes fonctions
// avec des données pré-calculées, sans fetch. Voir poc/build_static.py.
async function askApi(question) {
  const r = await fetch('/api/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  return r.json();
}

async function articlesApi() {
  return (await fetch('/api/articles')).json();
}

async function articleApi(ref) {
  return (await fetch('/api/article?ref=' + encodeURIComponent(ref))).json();
}
