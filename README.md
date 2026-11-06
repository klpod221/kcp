<div align="center">
    <h1>KCP: klpod221 Kontrol Panel & MCP Gateway</h1>
    <p>A unified, high-performance homelab management dashboard & Model Context Protocol (MCP) server built with Vue 3, Tailwind CSS v4, and FastAPI.</p>
    <img src="https://img.shields.io/github/last-commit/klpod221/kcp?style=for-the-badge&color=74c7ec&labelColor=111827" alt="Last Commit">
    <img src="https://img.shields.io/github/stars/klpod221/kcp?style=for-the-badge&color=facc15&labelColor=111827" alt="GitHub Stars">
    <img src="https://img.shields.io/github/repo-size/klpod221/kcp?style=for-the-badge&color=a78bfa&labelColor=111827" alt="Repo Size">
    <img src="https://img.shields.io/badge/License-MIT-34d399.svg?style=for-the-badge&labelColor=111827" alt="License">
    <br/>
    <a href="https://github.com/sponsors/klpod221">
        <img src="https://img.shields.io/badge/Sponsor-GitHub-ea4aaa?style=for-the-badge&logo=github&labelColor=111827" alt="GitHub Sponsors">
    </a>
    <a href="https://www.buymeacoffee.com/klpod221">
        <img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black&labelColor=111827" alt="Buy Me a Coffee">
    </a>
</div>

## 📝 Description

**klpod221 Kontrol Panel (KCP)** is a modern, unified homelab administration platform and Model Context Protocol (MCP) server. Built with a high-performance, dark-aesthetic single-page interface using **Vue 3 + Tailwind CSS v4** and an asynchronous **Python FastAPI + SQLAlchemy** backend, KCP combines real-time server telemetry, live Docker container orchestration, I/O bandwidth tracking, and complete media stack management into a single, cohesive pane of glass.

Beyond server administration, KCP serves as an enterprise-grade **MCP & AI Gateway**, offering 78 specialized homelab tools, OAuth 2.0 PKCE authorization, Personal Access Token (PAT) management, and an interactive AI Workspace for **Google Gemini**, **Claude**, and local AI agents.

Perfect for self-hosters, homelab enthusiasts, and DevOps engineers who want full visibility, total container control, and native AI integration for their home servers.

## 🚀 Table Of Content

- [📝 Description](#-description)
- [🚀 Table Of Content](#-table-of-content)
- [📸 Screenshots](#-screenshots)
  - [Server Overview \& Telemetry](#server-overview--telemetry)
  - [Docker Management \& Live Logs](#docker-management--live-logs)
  - [MCP Tools Catalog \& Playground](#mcp-tools-catalog--playground)
  - [OAuth 2.0 Consent Screen](#oauth-20-consent-screen)
- [✨ Features](#-features)
  - [🖥️ System Telemetry \& Hardware Monitor](#️-system-telemetry--hardware-monitor)
  - [🐳 Docker Orchestration \& Streaming Logs](#-docker-orchestration--streaming-logs)
  - [⚡ Live Transfers \& I/O Bandwidth](#-live-transfers--io-bandwidth)
  - [🎬 Homelab Media Stack Command Center](#-homelab-media-stack-command-center)
  - [🤖 MCP Server \& AI Gateway (78 Tools)](#-mcp-server--ai-gateway-78-tools)
  - [🔐 Security, RBAC \& OAuth 2.0 PKCE](#-security-rbac--oauth-20-pkce)
- [📡 Network Services \& Public Routing](#-network-services--public-routing)
- [📦 Installation & Deployment Guide](#-installation--deployment-guide)
  - [Prerequisites](#prerequisites)
  - [Step 1: Clone Repository](#step-1-clone-repository)
  - [Step 2: Environment Configuration](#step-2-environment-configuration)
  - [Step 3: Launch with Docker Compose](#step-3-launch-with-docker-compose)
- [🚀 Development](#-development)
  - [Frontend Development (Vue 3 + Vite)](#frontend-development-vue-3--vite)
  - [Backend Development (FastAPI + AsyncPG)](#backend-development-fastapi--asyncpg)
  - [Automated Testing (Pytest)](#automated-testing-pytest)
  - [Project Structure](#project-structure)
  - [Key Technologies](#key-technologies)
- [🔒 Security Considerations](#-security-considerations)
- [🤝 Contributing](#-contributing)
- [📝 License](#-license)
- [👤 Author](#-author)
- [🙏 Acknowledgments](#-acknowledgments)
- [📮 Support](#-support)
- [⭐ Star History](#-star-history)

## 📸 Screenshots

### Server Overview & Telemetry
![Server Overview](docs/public/screenshots/Overview.png)

### Docker Management & Live Logs
![Docker Management](docs/public/screenshots/Docker.png)

### MCP Tools Catalog & Playground
![Tools Catalog](docs/public/screenshots/Tools.png)

### OAuth 2.0 Consent Screen
![OAuth Consent Screen](docs/public/screenshots/Consent.png)

## ✨ Features

### 🖥️ System Telemetry & Hardware Monitor
- Real-time CPU usage, core clock frequencies, and multi-sensor thermal monitoring (`coretemp`, `pch_cannonlake`, `acpitz`).
- Dual-GPU metrics: Intel UHD 620 iGPU (VA-API hardware acceleration) and NVIDIA GeForce MX250 dGPU status.
- Memory & swap consumption, disk space utilization, and system uptime indicators.
- Live telemetry polling with micro-jitter suppression and tabular number alignment.

### 🐳 Docker Orchestration & Streaming Logs
- Inspect all containers running on the Docker host via direct UNIX socket integration.
- Instant container operations: **Start**, **Stop**, and **Restart** with real-time UI status updates.
- Full-featured **Live Container Logs** modal with auto-scroll lock, search filtering, and raw log export.
- Visual status badges: `running`, `healthy`, `restarting`, and `exited`.

### ⚡ Live Transfers & I/O Bandwidth
- Real-time disk read/write throughput (MB/s) and physical network bandwidth (DL/UL Mbit/s).
- Direct qBittorrent integration: inspect active torrents, seeds, peers, ETA, progress bars, and transmission rates.
- Rclone Google Drive VFS Cache monitor: active upload transfers, cache size tracking, and sliding 5-second transfer speed calculations.

### 🎬 Homelab Media Stack Command Center
- **Jellyfin**: Monitor active streaming sessions, transcode status, media bitrate, and user playback positions.
- **Jellyseerr**: Review, approve, and reject pending user requests for movies and TV shows.
- **Radarr & Sonarr**: Track active download queues, wanted releases, missing episodes, and calendar schedules.
- **Lidarr & Bazarr**: Monitor music queues, missing subtitle files, and audio library profiles.
- **Prowlarr**: View indexing status, sync status, and torrent indexer health metrics.

### 🤖 MCP Server & AI Gateway (78 Tools)
- Compliant with Model Context Protocol (MCP) Streamable HTTP and SSE specifications.
- **78 Production Tools**: Inspect hardware, control Docker, trigger media grabs, manage torrents, search Jellyfin, and interact with TriliumNext notes.
- Built-in **Tools Catalog & Playground**: Search tools, inspect JSON schemas, provide test arguments, and execute live calls directly from the browser.
- Interactive **AI Workspace**: Chat directly with AI models connected to your homelab tools.

### 🔐 Security, RBAC & OAuth 2.0 PKCE
- RFC 7636 OAuth 2.0 Authorization Server with Proof Key for Code Exchange (PKCE) for Google Gemini Connected Apps.
- Secure Consent Screen with granular scope selection (`mcp:read`, `mcp:tools`).
- Static Personal Access Token (PAT) generator (`klpod_pat_...`) with custom expiry and instant revocation.
- Signed, HTTP-only session cookies with role-based access control (Admin vs. Standard Users) and password change management.

## 📡 Network Services & Public Routing

| Service | Purpose | Internal Port | Public URL |
|:---|:---|:---:|:---|
| **KCP** | **klpod221 Kontrol Panel & MCP Gateway** | `8000` | [https://kcp.klpod221.com](https://kcp.klpod221.com) |
| **Homepage** | Personal Shortcut Portal | `3000` | [https://klpod221.com](https://klpod221.com) |
| **Jellyfin** | Media Streaming & Playback | `8096` | [https://media.klpod221.com](https://media.klpod221.com) |
| **Jellyseerr** | Media Discovery & Requests | `5055` | [https://request.klpod221.com](https://request.klpod221.com) |
| **TriliumNext** | Personal Knowledge Base & Notes | `8080` | [https://notes.klpod221.com](https://notes.klpod221.com) |
| **qBittorrent** | Torrent Client | `8080` | Internal (`main_nets`) |
| **Radarr** | Movie Management | `7878` | Internal (`main_nets`) |
| **Sonarr** | TV Show & Anime Management | `8989` | Internal (`main_nets`) |
| **Lidarr** | Music Library Management | `8686` | Internal (`main_nets`) |
| **Bazarr** | Subtitle Management | `6767` | Internal (`main_nets`) |
| **Prowlarr** | Indexer Manager | `9696` | Internal (`main_nets`) |
| **PostgreSQL** | Primary Relational Database | `5432` | Internal (`main_nets`) |

## 📦 Installation & Deployment Guide

### Prerequisites
- **Docker Engine** (v24.0 or higher) & **Docker Compose** (v2.20+)
- Access to Docker socket (`/var/run/docker.sock`)
- Cloudflare Tunnel (optional, for secure zero-trust external domain exposure)

### Step 1: Clone Repository
```bash
git clone https://github.com/klpod221/kcp.git
cd kcp
```

### Step 2: Environment Configuration
Copy the provided `.env.example` template and configure your secrets:
```bash
cp .env.example .env
nano .env
```
Ensure you generate strong cryptographic secrets:
```bash
# Generate secure keys for JWT and sessions:
openssl rand -hex 32
```

### Step 3: Launch with Docker Compose
```bash
# Build and launch all 16 homelab containers in background:
docker compose up -d

# Verify container health:
docker compose ps
```
Access the control panel at `http://localhost:8000` or via your configured domain.

## 🚀 Development

### Frontend Development (Vue 3 + Vite)
```bash
cd frontend
npm install
npm run dev
```

### Backend Development (FastAPI + AsyncPG)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Automated Testing (Pytest)
Run the automated test suite directly inside the Docker container:
```bash
docker exec kcp pytest tests/ -v
```

### Project Structure

```text
kcp/
├── .dockerignore                  # Docker build context exclusions
├── .env.example                   # Sanitized configuration template
├── .gitignore                     # Git tracking exclusions
├── Dockerfile                     # Multi-stage production container build
├── README.md                      # Project documentation
├── docker-compose.yaml            # Complete 16-service homelab stack
├── main.py                        # FastAPI entrypoint
├── requirements.txt               # Backend Python dependencies
├── app/                           # Backend Application Source
│   ├── api/routes/                # Endpoints (Admin, Docker, Health, MCP, OAuth, System)
│   ├── core/                      # Security, Dependencies, JWT, Auth, Logging
│   ├── db/                        # SQLAlchemy Async Models & Migrations
│   ├── mcp/                       # 78 MCP Tools & Streamable HTTP Session Manager
│   └── services/                  # Hardware telemetry, Docker API, and Service Wrappers
├── frontend/                      # Frontend SPA Source
│   ├── src/                       # Vue 3 Components, Views, Pinia Stores, & Tailwind styles
│   ├── index.html                 # HTML Entrypoint
│   └── vite.config.js             # Vite build pipeline with asset hash busting
├── services/                      # Homelab service configuration templates & init scripts
│   ├── komepage/config.yml.example
│   └── postgres/init-scripts/01-init-dbs.sh
└── tests/                         # Pytest test suite (OAuth, Admin API, MCP protocol)
```

### Key Technologies

| Layer | Technology | Purpose |
|:---|:---|:---|
| **Frontend Framework** | Vue 3 (Composition API) | Reactive Single-Page Application |
| **State Management** | Pinia | Centralized client state |
| **Styling** | Tailwind CSS v4 | Carbon & Zinc dark aesthetic |
| **Icons & Typography** | Lucide Vue Next, Inter, JetBrains Mono | UI iconography and tabular numbers |
| **Backend Framework** | FastAPI + Uvicorn | Asynchronous, high-throughput REST API |
| **AI Protocol** | Model Context Protocol (MCP) | LLM tool integration protocol |
| **Database ORM** | SQLAlchemy 2.0 (Async) + asyncpg | Asynchronous PostgreSQL database layer |
| **Security & Auth** | OAuth 2.0 PKCE, PyJWT, Passlib, Argon2 | Enterprise-grade authentication |
| **Orchestration** | Docker & Docker Compose | Multi-container homelab infrastructure |

## 🔒 Security Considerations

- **Strict Environment Isolation**: All production secrets, passwords, and external API keys reside solely in `.env`, strictly excluded from version control.
- **Cryptographic Token Hashing**: Personal Access Tokens (PAT) and authorization codes are hashed at rest using SHA-256 before database insertion.
- **CORS & DNS Rebinding Protection**: Streamable HTTP endpoints enforce origin verification and RFC-compliant preflight checks.
- **Session Protection**: Administrative web sessions rely on signed, HTTP-only, `SameSite=Lax` cookies with configurable expiry and auto-lock.
- **Read-Only Volume Mounts**: Critical system directories (`/etc/os-release`, host media mounts) are mounted with `read_only: true` constraints.

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the [MIT License](LICENSE) - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Bùi Thanh Xuân (klpod221)**

- Website: [klpod221.com](https://klpod221.com)
- GitHub: [@klpod221](https://github.com/klpod221)
- Email: [klpod221@gmail.com](mailto:klpod221@gmail.com)

## 🙏 Acknowledgments

- **FastAPI** - For the high-performance async Python web framework
- **Vue.js** - For the delightful frontend reactive framework
- **Tailwind CSS** - For the utility-first CSS styling engine
- **Model Context Protocol (MCP)** - For the open standard enabling AI agent tool integration
- **Lucide Icons** - For the clean, consistent icon library

## 📮 Support

If you encounter any issues or have questions:

1. Check existing [Issues](https://github.com/klpod221/kcp/issues)
2. Create a new issue with reproduction steps and logs
3. Contact via email: [klpod221@gmail.com](mailto:klpod221@gmail.com)

## ⭐ Star History

<a href="https://www.star-history.com/?repos=klpod221%2Fkcp&type=date&legend=bottom-right">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=klpod221/kcp&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=klpod221/kcp&type=date&theme=dark&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=klpod221/kcp&type=date&legend=top-left" />
 </picture>
</a>

---

<div align="center">
    <p>Made with ❤️ by klpod221</p>
    <p>⭐ Star this repository if you find it helpful!</p>
</div>
