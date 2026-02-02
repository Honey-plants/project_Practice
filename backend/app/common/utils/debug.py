import traceback

def log_exception(tag: str, e: Exception) -> None:
    print(f"\n🔥[{tag}] {type(e).__name__}: {e}")
    print(traceback.format_exc())
    print("🔥 end traceback\n")
