from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlmodel import Session, select

from common.db import create_db_and_tables, get_session
from common.models import Link, Click


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="tracker-service", lifespan=lifespan)


@app.get("/health")
def health():
    return {"ok": True, "service": "tracker"}


def _client_ip(request: Request) -> tuple[str | None, str | None]:
    xff = request.headers.get("x-forwarded-for")
    ip = request.client.host if request.client else None
    return ip, xff


@app.get("/t/{code}")
def track_and_redirect(
    code: str,
    request: Request,
    js: int = 0,
    session: Session = Depends(get_session),
):
    link = session.exec(select(Link).where(Link.code == code)).first()
    if not link:
        raise HTTPException(status_code=404, detail="Unknown code")

    ip, xff = _client_ip(request)
    headers = dict(request.headers)
    query = dict(request.query_params)

    click = Click(
        link_id=link.id,
        ip=ip,
        forwarded_for=xff,
        method=request.method,
        path=str(request.url.path),
        user_agent=request.headers.get("user-agent"),
        accept_language=request.headers.get("accept-language"),
        referer=request.headers.get("referer"),
        headers=headers,
        query=query,
    )
    session.add(click)
    session.commit()
    session.refresh(click)

    if js == 1:
       
        html = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>tracking...</title>
  <meta name="referrer" content="strict-origin-when-cross-origin">
  <style>
    body {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      background: #0b0f17; color: #d6f0ff; padding: 24px;
    }}
    .box {{ border: 1px dashed #3aa3ff; padding: 16px; max-width: 900px; }}
    code {{ color: #7dffb2; }}
  </style>
</head>
<body>
  <div class="box">
    <div>Ловим технику, держись…</div>
    <div>click_id: <code>{click.id}</code></div>
    <div>redirect -> <code>{link.target_url}</code></div>
  </div>

<script>
(function() {{
  const clickId = {click.id};
  const target = {link.target_url!r};

  const payload = {{
    ts: new Date().toISOString(),
    navigator: {{
      userAgent: navigator.userAgent,
      language: navigator.language,
      languages: navigator.languages,
      platform: navigator.platform,
      cookieEnabled: navigator.cookieEnabled,
      doNotTrack: navigator.doNotTrack,
      hardwareConcurrency: navigator.hardwareConcurrency,
      deviceMemory: navigator.deviceMemory,
      maxTouchPoints: navigator.maxTouchPoints
    }},
    screen: {{
      width: screen.width,
      height: screen.height,
      colorDepth: screen.colorDepth,
      pixelRatio: window.devicePixelRatio
    }},
    viewport: {{
      innerWidth: window.innerWidth,
      innerHeight: window.innerHeight
    }},
    tz: (Intl.DateTimeFormat().resolvedOptions() || {{}}).timeZone || null
  }};

  try {{
    const blob = new Blob([JSON.stringify(payload)], {{ type: "application/json" }});
    navigator.sendBeacon(`/clicks/${{clickId}}/client`, blob);
  }} catch (e) {{
    // no-op
  }}

  setTimeout(() => {{ window.location.href = target; }}, 50);
}})();
</script>
</body>
</html>
"""
        return HTMLResponse(html)

    return RedirectResponse(link.target_url, status_code=307)


@app.post("/clicks/{click_id}/client")
async def attach_client_info(
    click_id: int,
    request: Request,
    session: Session = Depends(get_session),
):
    click = session.get(Click, click_id)
    if not click:
        raise HTTPException(status_code=404, detail="Unknown click_id")

    data: Any = await request.json()
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="JSON object expected")

    click.client = data
    session.add(click)
    session.commit()
    return {"ok": True}