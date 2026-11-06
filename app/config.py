from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application and Server Configuration for klpod221 control panel (KCP)."""

    APP_NAME: str = "klpod221 Kontrol Panel"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # Server Host & Port
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Public Base URL (for Cloudflare Tunnel)
    BASE_URL: str = "https://kcp.klpod221.com"

    # Database Configuration (PostgreSQL by default, SQLite fallback for local test)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/mcp_db"

    # MCP Configurations
    MCP_SERVER_NAME: str = "klpod221-mcp"
    MCP_SERVER_DESCRIPTION: str = (
        "Private personal MCP server for klpod221's home-lab: Server Hardware Monitor, "
        "Radarr, Sonarr, Lidarr, Prowlarr, Bazarr, Jellyfin, Jellyseerr, qBittorrent, and TriliumNext."
    )
    MCP_SERVER_INSTRUCTIONS: str = (
        "Use this connector to monitor klpod221's server hardware (CPU, GPU, RAM, temperatures, disk), "
        "manage movies (Radarr), TV shows/anime (Sonarr), music (Lidarr), torrent indexers (Prowlarr), "
        "subtitles (Bazarr), media playback/libraries (Jellyfin), media requests/discovery (Jellyseerr), "
        "torrent downloads (qBittorrent), and personal notes/knowledge base (TriliumNext)."
    )
    MCP_MESSAGE_ENDPOINT: str = "/mcp/message"

    # Security: JWT & Session Signing Keys
    JWT_SECRET_KEY: str = "change_me_to_a_secure_jwt_secret_in_production"
    JWT_ALGORITHM: str = "HS256"
    SESSION_SECRET_KEY: str = "change_me_to_a_secure_session_secret_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    COOKIE_SECURE: bool = True

    # Default Seed Credentials
    DEFAULT_ADMIN_USERNAME: str = "klpod221"
    DEFAULT_ADMIN_PASSWORD: str = "ChangeMeAdminPassword123!"
    DEFAULT_ADMIN_EMAIL: str = "klpod221@gmail.com"

    # Default OAuth Client (for Google Gemini)
    DEFAULT_CLIENT_ID: str = "gemini_client"
    DEFAULT_CLIENT_SECRET: str = "gemini_secret_2026"
    DEFAULT_CLIENT_NAME: str = "Google Gemini"
    DEFAULT_CLIENT_REDIRECT_URIS: list[str] = [
        "https://oauth.google.com/callback",
        "https://gemini.google.com/oauth/callback",
        "https://oauth.pstmn.io/v1/callback",
    ]

    # Home-Lab & Media Stack Service Configurations
    HOMEPAGE_URL: str = "http://homepage:3000"

    RADARR_URL: str = "http://radarr:7878"
    RADARR_API_KEY: str = ""
    RADARR_DEFAULT_ROOT_FOLDER: str = "/data/media/Movies"
    RADARR_DEFAULT_QUALITY_PROFILE_ID: int = 7

    SONARR_URL: str = "http://sonarr:8989"
    SONARR_API_KEY: str = ""
    SONARR_DEFAULT_ROOT_FOLDER: str = "/data/media/TV_Shows"
    SONARR_DEFAULT_QUALITY_PROFILE_ID: int = 7

    LIDARR_URL: str = "http://lidarr:8686"
    LIDARR_API_KEY: str = ""
    LIDARR_DEFAULT_ROOT_FOLDER: str = "/data/media/Music"
    LIDARR_DEFAULT_QUALITY_PROFILE_ID: int = 1
    LIDARR_DEFAULT_METADATA_PROFILE_ID: int = 1

    PROWLARR_URL: str = "http://prowlarr:9696"
    PROWLARR_API_KEY: str = ""

    BAZARR_URL: str = "http://bazarr:6767"
    BAZARR_API_KEY: str = ""

    JELLYFIN_URL: str = "http://jellyfin:8096"
    JELLYFIN_EXTERNAL_URL: str = "https://media.klpod221.com"
    JELLYFIN_API_KEY: str = ""

    JELLYSEERR_URL: str = "http://jellyseerr:5055"
    JELLYSEERR_EXTERNAL_URL: str = "https://request.klpod221.com"
    JELLYSEERR_API_KEY: str = ""

    QBITTORRENT_URL: str = "http://qbittorrent:8080"
    QBITTORRENT_USERNAME: str = "klpod221"
    QBITTORRENT_PASSWORD: str = ""

    TRILIUM_URL: str = "http://triliumnext:8080"
    TRILIUM_ETAPI_TOKEN: str = ""
    TRILIUM_PASSWORD: str = ""

    RCLONE_RC_URL: str = "http://host.docker.internal:5573"
    RCLONE_MOUNT_PATH: str = "/data/media"

    HTTP_TIMEOUT_SECONDS: float = 25.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
