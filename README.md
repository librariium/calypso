<!-- PROJECT SUMMARY -->
<div align="center">
  <h1 align="center">Calypso 🌊</h1>

  <p align="center">
    A semantic book recommender that uncovers the "vibe" of your next favorite read with Vector Embeddings and AI.
    <br>
    <a href="https://github.com/librariium/calypso/issues">» submit a suggestion </a>
    ·
    <a href="https://github.com/librariium/calypso/issues">» report a bug </a>
    ·
    <a href="https://github.com/librariium/calypso">» contact </a>
  </p>

  <div align="center">

![GitHub forks](https://img.shields.io/github/forks/librariium/calypso?style=social) ![GitHub stars](https://img.shields.io/github/stars/librariium/calypso?style=social)

[![CI](https://github.com/librariium/calypso/actions/workflows/push_on_main.yml/badge.svg)](https://github.com/librariium/calypso/actions/workflows/push_on_main.yml)
![GitHub Pull Request (open)](https://img.shields.io/github/issues-pr/librariium/calypso?color=blue) ![GitHub last commit](https://img.shields.io/github/last-commit/librariium/calypso?color=pink) ![GitHub License](https://img.shields.io/github/license/librariium/calypso?color=green) ![contributions welcome](https://img.shields.io/badge/contributions-welcome-purple.svg?style=flat)

  </div>
</div>

<details open="open">
  <summary><h2 style="display: inline-block">🕹 Table of Content</h2></summary>
  <ol>
    <li>
      <a href="#🌻-about">About</a>
      <ul>
        <li><a href="#🔧-tech-stack">Tech Stack</a></li>
        <li><a href="#🍄-features">Features</a></li>
      </ul>
    </li>
    <li>
      <a href="#🌵-documentation">Documentation</a>
      <ul>
        <li><a href="#🍯-setup">Setup</a></li>
        <li><a href="#🍎-development">Development</a></li>
      </ul>
    </li>
    <li><a href="#🌾-contributing">Contributing</a></li>
    <li><a href="#📜-license">License</a></li>
  </ol>
</details>

## :sunflower: About
A "vibe matcher" for books, integrating modern AI/ML workflows (Python/FastAPI) with consumer-facing web applications (Next.js). Calypso uses semantic search to understand the emotional context of a user's request. By leveraging vector embeddings (`all-MiniLM-L6-v2`) and the `Hardcover.app` API, it allows users to search for natural language queries like *"A sci-fi about loneliness in space"* or *"A mystery that feels like a rainy day in London"* and retrieve statistically relevant matches.

### :hammer_and_wrench: Tech Stack

#### :heavy_plus_sign: Development Tools

- [x] **Visual Studio Code** : IDE
- [x] **Git & GitHub** : Version control
- [x] **Postman** : API endpoint testing
- [x] **Swagger UI** : API documentation & interactive testing

#### :heavy_plus_sign: Backend (AI & API)

- [x] **FastAPI/Python** : High-performance web framework
- [x] **LangChain** : Orchestration for AI models
- [x] **Pinecone** : Vector Database for semantic indexing
- [x] **Hardcover API** : Live metadata fetch (GraphQL)
- [x] **Sentence Transformers** : Local embedding generation

#### :heavy_plus_sign: Frontend

- [x] **Next.js 14+** : React
- [x] **TypeScript** : Static type checking & interfaces
- [x] **Tailwind CSS** : Utility-first styling system
- [x] **Axios/Fetch** : HTTP client for API requests

#### :heavy_plus_sign: DevOps

- [x] **Vercel** : Frontend Deployment
- [x] **Render / Railway** : Backend Deployment
- [x] **Kaggle** : Dataset sourcing

### :mushroom: Features

#### :heavy_plus_sign: Semantic Search Engine

- [x] **Natural Language Querying:** Users can type sentences describing a plot or feeling, not just keywords.
- [x] **Vector-Based Retrieval:** Uses cosine similarity to find books with matching "vibes" in the vector space.

#### :heavy_plus_sign: Hybrid Data Pipeline

- [x] **Static Training:** Model trained on dataset.
- [x] **Live Enrichment:** Real-time fetching of book covers, ratings, and author data via Hardcover's GraphQL API to ensure the UI is always up-to-date.

## :cactus: Documentation

### :honey_pot: Setup

1. **Clone the repository**
   ```bash
    git clone [https://github.com/librariium/calypso.git](https://github.com/librariium/calypso.git)
    cd calypso
   ```

2. **Backend**
   ```bash
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
   ```

3. **Frontend**
   ```bash
    cd ../frontend
    npm install
   ```

### :apple: Development
<!-- Add development details here -->
* [ ] Run Backend: cd backend && uvicorn main:app --reload
* [ ] Run Frontend: cd frontend && npm run dev
* [ ] API Docs: Access Swagger UI at http://localhost:8000/docs

<!-- CONTRIBUTING -->
## :ear_of_rice: Contributing
<!-- Add contribution guidelines here -->
> 1. Fork the Project
> 2. Create your Branch (`git checkout -b my-branch`)
> 3. Commit your Changes (`git commit -m 'add my contribution'`)
> 4. Push to the Branch (`git push --set-upstream origin my-branch`)
> 5. Open a Pull Request

<!-- LICENSE -->
## :pencil: License
<!-- Add license information here -->
This project is licensed under [LICENSE](https://opensource.org/licenses).

<!-- Gratitude to [source]() for the inspiration and insights. -->

<!-- ACKNOWLEDGEMENTS -->
<!-- ## Acknowledgements -->
