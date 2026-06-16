# Media Support and Long Prompts — Design

## Summary

Add image/video support and long-prompt handling to the Telegram OpenCode bot.

## Changes

### 1. Media (photos/videos)

**Flow:**
1. User sends photo/video to bot
2. Bot gets `file_id` + `file_path` via `bot.get_file()`
3. Bot sends command to agent with `media` field: `[{file_id, file_path}]`
4. Agent downloads file from `https://api.telegram.org/file/bot<TOKEN>/<file_path>`
5. Agent inserts local path into the prompt and calls opencode
6. If the model supports vision, it "sees" the file

**Agent protocol extension:**
```json
{
  "cmd": "run",
  "message": "Опиши это изображение",
  "session_id": "",
  "media": [{"file_id": "AgAC...", "file_path": "photos/file.jpg"}]
}
```

**Agent template:**
- Generated with `BOT_TOKEN` embedded at agent creation time
- `run_opencode` checks for `media`, downloads each file before calling opencode
- Local file path is inserted into the message text

**Handlers:**
- `F.photo` — takes largest photo (`message.photo[-1]`)
- `F.video` — takes the video file
- Both respect existing `message.caption` as the prompt text

### 2. Long prompts

**Problem:** Windows CLI arg limit (~8191 chars). Current code passes message as positional arg to `opencode run`.

**Solution:** If message > 2000 chars, write to temp file, pipe via PowerShell:
```
Get-Content "<tempfile>" -Raw | opencode run --dangerously-skip-permissions
```

Applied in both:
- `generate_agent_py` template (agent-side)
- `opencode_client.py` (server-side direct use)

### Files modified

| File | Changes |
|------|---------|
| `bot.py` | `F.photo`, `F.video` handlers; `ask_agent` passes `media`; `generate_agent_py` adds BOT_TOKEN, media download, long prompt handling |
| `opencode_client.py` | `ask_opencode` long prompt → temp file + pipe |
