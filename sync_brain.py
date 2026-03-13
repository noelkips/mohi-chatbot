from app.services.knowledge import run_automated_sync


if __name__ == "__main__":
    run_automated_sync(reset_db=True)
