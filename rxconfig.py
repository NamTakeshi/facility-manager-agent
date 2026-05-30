import reflex as rx

config = rx.Config(
    app_name="facility_manager_agent",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)