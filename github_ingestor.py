import json
import re
import sys
import urllib.request
import urllib.error

def fetch_issue_context(issue_url: str):
    """Scrapes live Title, Body, and Labels from a public GitHub issue URL."""
    match = re.search(r"github\.com/([^/]+)/([^/]+)/issues/(\d+)", issue_url)
    if not match:
        return None, "Invalid GitHub Issue URL. Expected: https://github.com/owner/repo/issues/123"

    owner, repo, issue_num = match.groups()
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_num}"

    try:
        req = urllib.request.Request(
            api_url,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Axiom-Autonomous-Engine/1.0"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310
            data = json.loads(resp.read().decode("utf-8"))
            title = data.get("title", "Untitled Issue")
            body = data.get("body") or "No description provided."
            labels = ", ".join(lbl.get("name", "") for lbl in data.get("labels", []))

            context = (
                f"[GitHub Issue #{issue_num} from {owner}/{repo}]\n"
                f"Title: {title}\n"
                f"Labels: {labels}\n\n"
                f"Issue Specification:\n{body}\n"
            )
            return context, None
    except urllib.error.HTTPError as e:
        return None, f"GitHub API returned HTTP {e.code} for {api_url}"
    except Exception as e:
        return None, str(e)
