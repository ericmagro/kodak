"""Health check HTTP server for Railway monitoring."""

import asyncio
import logging
from aiohttp import web
import aiohttp_cors

logger = logging.getLogger('kodak.health')


async def health_check(request):
    """Simple health check endpoint."""
    return web.json_response({
        'status': 'healthy',
        'service': 'kodak-bot',
        'timestamp': request.headers.get('X-Request-Start', 'unknown')
    })


async def create_health_server(port: int = 8080):
    """Create and return the health check server."""
    app = web.Application()

    # Setup CORS
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })

    # Add health check route
    health_route = app.router.add_get('/health', health_check)
    cors.add(health_route)

    # Add root route that redirects to health
    async def root_redirect(request):
        return web.json_response({
            'message': 'Kodak Discord Bot',
            'health': '/health'
        })

    root_route = app.router.add_get('/', root_redirect)
    cors.add(root_route)

    return app, port


async def start_health_server(port: int = 8080):
    """Start the health check server."""
    app, server_port = await create_health_server(port)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, '0.0.0.0', server_port)
    await site.start()

    logger.info(f"Health check server running on port {server_port}")
    return runner


if __name__ == "__main__":
    # For testing the health server standalone
    async def main():
        runner = await start_health_server()
        try:
            await asyncio.Event().wait()  # Run forever
        except KeyboardInterrupt:
            await runner.cleanup()

    asyncio.run(main())