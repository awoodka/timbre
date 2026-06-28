# Timbre — Docker workflows. Dev is the default (hot-reload + bind-mounts).
# Rebuild images ONLY when dependencies change (requirements.txt / package.json);
# code is bind-mounted, so day-to-day edits need no rebuild. `make rebuild` is the
# one command that prevents stale-image drift (a missing dep baked into an old image).

.PHONY: up rebuild logs down ps prod prod-down

# Start the dev stack (builds images if they don't exist yet, then runs detached).
up:
	docker compose up -d

# Rebuild images to pick up dependency changes, then restart. Run after editing
# requirements.txt or package.json.
rebuild:
	docker compose build
	docker compose up -d

# Tail logs for all services.
logs:
	docker compose logs -f

# Stop + remove containers (the pgdata volume persists, so data survives).
down:
	docker compose down

# Service status + health.
ps:
	docker compose ps

# Production bring-up: immutable images (no bind-mounts), no hot-reload, hardened
# cookies. Requires a real SECRET_KEY and COOKIE_SECURE=true in .env. Expose it with
# a Cloudflare Tunnel pointed at :3000 — `cloudflared tunnel --url http://localhost:3000`.
prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Stop the production stack.
prod-down:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down
