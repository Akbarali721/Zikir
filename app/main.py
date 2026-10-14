from contextlib import asynccontextmanager

from pathlib import Path



from fastapi import FastAPI, HTTPException

from fastapi.responses import FileResponse

from fastapi.staticfiles import StaticFiles



from app.api import admin, profile, retention, stats, tasbeh, telegram_bot, web

from app.bot.setup import configure_webhook, shutdown_bot

from app.config import get_settings

from app.db.database import AsyncSessionLocal

from app.services.progress_service import ensure_global_progress





@asynccontextmanager

async def lifespan(app: FastAPI):

    async with AsyncSessionLocal() as session:

        try:

            await ensure_global_progress(session)

            await session.commit()

        except Exception:

            await session.rollback()

    settings = get_settings()

    try:

        await configure_webhook(settings)

    except Exception:

        pass

    yield

    await shutdown_bot()





def create_app() -> FastAPI:

    settings = get_settings()

    app = FastAPI(title="Million Istighfor", debug=settings.debug, lifespan=lifespan)



    static_dir = Path(__file__).resolve().parent / "static"

    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")



    app.include_router(tasbeh.router)

    app.include_router(stats.router)

    app.include_router(profile.router)

    app.include_router(retention.router)

    app.include_router(admin.router)

    app.include_router(telegram_bot.router)



    frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"



    if frontend_dist.is_dir() and (frontend_dist / "index.html").is_file():

        assets_dir = frontend_dist / "assets"

        if assets_dir.is_dir():

            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="vue-assets")



        @app.get("/")

        async def spa_root():

            return FileResponse(frontend_dist / "index.html")



        @app.get("/welcome")

        @app.get("/profile")

        @app.get("/tasbeh")

        @app.get("/admin")
        @app.get("/admin/forbidden")

        async def spa_shell_routes():

            return FileResponse(frontend_dist / "index.html")



        @app.get("/{full_path:path}")

        async def spa_fallback(full_path: str):

            if full_path.startswith("api/"):

                raise HTTPException(status_code=404, detail="Not found")

            candidate = frontend_dist / full_path

            if candidate.is_file():

                return FileResponse(candidate)

            if "." not in full_path:

                return FileResponse(frontend_dist / "index.html")

            raise HTTPException(status_code=404, detail="Not found")

    else:

        app.include_router(web.router)

    return app





app = create_app()

