# klpod221 Kontrol Panel (KCP)

Bảng điều khiển quản trị duy nhất cho toàn bộ máy chủ Homelab **klpod221-server**, tích hợp:
- **Quản trị Máy chủ**: Giám sát phần cứng thời gian thực (CPU, iGPU Intel UHD 620, dGPU NVIDIA MX250, nhiệt độ đa cảm biến, RAM, Disk), quản trị Docker Containers trực tiếp (Start / Stop / Restart / Live Logs) qua socket Docker host.
- **Tiến trình & Băng thông (Live Transfers & I/O)**: Giám sát tốc độ Đọc/Ghi đĩa thực tế, Băng thông mạng DL/UL, quản lý torrent qBittorrent trực tiếp và giám sát tiến trình upload/download Rclone Google Drive VFS Cache với thuật toán tính tốc độ trượt 5 giây.
- **Trung tâm Dịch vụ Homelab**: Xem phiên phát Jellyfin, duyệt/từ chối yêu cầu Jellyseerr, theo dõi hàng đợi Radarr / Sonarr / Lidarr, kiểm tra phụ đề Bazarr và indexers Prowlarr.
- **Phân khu MCP & AI Gateway**: Cổng giao tiếp Model Context Protocol (78 Tools) cho Claude / Gemini / Open WebUI, cấp phát Static PAT (`klpod_pat_...`), OAuth 2.0 Authorization Server và AI Chat Workspace.

---

## 1. Danh sách Dịch vụ & Cổng truy cập

| Dịch vụ | Mục đích | Cổng nội bộ | Tên miền Công khai |
| :--- | :--- | :--- | :--- |
| **KCP** | **klpod221 Kontrol Panel** | `8000` | [https://kcp.klpod221.com](https://kcp.klpod221.com) |
| **Homepage** | Dashboard lối tắt cá nhân | `3000` | [https://klpod221.com](https://klpod221.com) |
| **Jellyfin** | Xem phim & Nghe nhạc | `8096` | [https://media.klpod221.com](https://media.klpod221.com) |
| **Jellyseerr** | Tìm & Yêu cầu phim | `5055` | [https://request.klpod221.com](https://request.klpod221.com) |
| **TriliumNext** | Ghi chú & Tri thức | `8080` (trilium) | [https://notes.klpod221.com](https://notes.klpod221.com) |
| **qBittorrent** | Tải torrent | `8080` | `http://klpod221-server:8080` |
| **Radarr** | Tải phim lẻ | `7878` | `http://klpod221-server:7878` |
| **Sonarr** | Tải phim bộ / Anime | `8989` | `http://klpod221-server:8989` |
| **Lidarr** | Tải nhạc Lossless | `8686` | `http://klpod221-server:8686` |
| **Bazarr** | Quản lý phụ đề | `6767` | `http://klpod221-server:6767` |
| **Prowlarr** | Quản lý Indexers | `9696` | `http://klpod221-server:9696` |
| **PostgreSQL** | Cơ sở dữ liệu chính | `5432` | Nội bộ mạng `main_nets` |

---

## 2. Cấu trúc Thư mục Dự án

```text
/home/klpod221/server-config/
├── .dockerignore             # Tối ưu build context Docker
├── .env                      # Cấu hình môi trường duy nhất cho toàn server & KCP
├── Dockerfile                # Multi-stage build đóng gói KCP (Vue 3 + Tailwind v4 + FastAPI)
├── docker-compose.yaml       # Toàn bộ stack 16 services
├── main.py                   # Entrypoint khởi chạy KCP
├── requirements.txt          # Python dependencies
├── app/                      # Backend FastAPI + MCP Server
│   ├── api/routes/           # Admin, Docker, System, Transfers, MCP, OAuth2, Health
│   ├── core/                 # Dependencies, Security, Auth, Logging
│   ├── db/                   # SQLAlchemy Models & Async Session
│   ├── mcp/                  # 78 MCP Tools (Hardware, Docker, Media Stack, Rclone, Trilium)
│   └── services/             # DockerService, SystemMonitorService, *arr, Jellyfin, qBit, Rclone
├── frontend/                 # Frontend SPA (100% Pure JS + Vue 3 + Pinia + Tailwind CSS v4)
├── services/                 # Toàn bộ dữ liệu cấu hình 11 container vệ tinh
│   ├── bazarr/
│   ├── jellyfin/
│   ├── jellyseerr/
│   ├── komepage/
│   ├── lidarr/
│   ├── postgres/
│   ├── prowlarr/
│   ├── qbittorrent/
│   ├── radarr/
│   ├── sonarr/
│   └── triliumnext/
└── downloads/                # Thư mục tải về chung
```

---

## 3. Khởi chạy & Kiểm thử

```bash
# Khởi động toàn bộ cụm máy chủ
docker compose up -d

# Chạy bộ kiểm thử tự động
docker exec kcp pytest tests/ -v
```
