# Local setup: PlexAniSync + Tautulli (Windows)

This checkout is wired up to the Tautulli instance running on this machine
(`http://127.0.0.1:8181`) so that finishing an episode in the **Anime TVDB**
library updates the AniList account automatically.

## How it works

```
Plex playback stops
  -> Tautulli "on_stop" notification (Playback Stop trigger)
     -> notification agent "PlexAniSync - Sync AniList" (notifier id 2)
        -> TautulliSyncHelper.pyw   (launcher, runs headless via pythonw)
           -> .venv\Scripts\pythonw.exe TautulliSyncHelper.py "<show name>"
              -> TautulliSyncHelper.py (upstream helper)
                 -> reads settings.ini, syncs that one show to AniList
```

Only the show that was just watched is synced, which keeps the run fast.

## Files

| Path | Purpose |
| --- | --- |
| `settings.ini` | Plex + AniList credentials. Gitignored, never commit it. |
| `TautulliSyncHelper.pyw` | Local launcher. Tautulli runs `.pyw` files with `pythonw` (no console window); this launcher hands over to the virtualenv interpreter that actually has the dependencies installed. |
| `.venv/` | Virtualenv with the pinned `requirements.txt`. Gitignored. |
| `logs/tautulli_sync.log` | Output of every sync run. Gitignored. |
| `custom_mappings.yaml` | Optional manual Plex title -> AniList ID mappings. Gitignored. Copy `custom_mappings.yaml.example` to create it. |

## Tautulli notification agent

Configured through the Tautulli API (`add_notifier_config` / `set_notifier_config`),
so it is visible and editable in the Tautulli UI under
**Settings -> Notification Agents -> PlexAniSync - Sync AniList**.

| Setting | Value |
| --- | --- |
| Agent | Script (`agent_id` 15) |
| Script folder | this repository |
| Script file | `TautulliSyncHelper.pyw` |
| Timeout | 300 seconds |
| Trigger | Playback Stop (`on_stop`) |
| Argument | `"{show_name}"` |
| Condition | `library_name` is `Anime TVDB` |
| Condition | `progress_percent` is greater than `90` |

Tautulli already had **Settings -> Notifications & Newsletters -> "Allow Playback
Stop Notifications Exceeding Watched Percent"** enabled (`notify_consecutive = 1`),
which the PlexAniSync wiki requires, so no change was needed there.

## Running it by hand

```powershell
# single show, uses settings.ini from this folder
.\.venv\Scripts\python.exe TautulliSyncHelper.py "Akiba Maid War"

# everything at once
.\.venv\Scripts\python.exe PlexAniSync.py
```

## Notes

- The AniList access token is only valid for **one year**. Get a new one from
  <https://anilist.co/api/v2/oauth/authorize?client_id=1549&response_type=token>
  and replace `access_token` in `settings.ini`.
- `skip_list_update = True` in `settings.ini` means "match but do not write".
  Set it to `False` to let the sync actually update AniList.
- The **Anime TVDB** library is matched with the TheTVDB agent, so PlexAniSync
  falls back to title/year matching against AniList. Switching that library to
  the HAMA agent gives it exact AniList IDs and therefore much better matches.
- The trigger only fires for the **Anime TVDB** library. To also sync the
  **Anime Movies** library, add `Anime Movies` to the `library_name` condition
  of the notification agent.
