from django.utils import timezone

def gen_running_no(prefix: str, last_no: str | None) -> str:
    # INV-00001 style
    if not last_no:
        return f"{prefix}-00001"
    try:
        n = int(last_no.split("-")[-1])
    except Exception:
        n = 0
    return f"{prefix}-{n+1:05d}"

def now_str():
    return timezone.localtime(timezone.now()).strftime("%Y-%m-%d %H:%M")
