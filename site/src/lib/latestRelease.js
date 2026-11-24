// The newest SpotiParty release on GitHub: its version and the Windows and Mac downloads.
// The links work without the API too: the Mac file has a fixed name, and Windows falls back to the release page.
import { useEffect, useState } from "react";

const REPO = "CodeAura/SpotiParty";
const FALLBACK = {
  version: "",
  exe: `https://github.com/${REPO}/releases/latest`,
  dmg: `https://github.com/${REPO}/releases/latest/download/SpotiParty-macos-apple-silicon.dmg`,
  intel: `https://github.com/${REPO}/releases/latest/download/SpotiParty-macos-intel.dmg`,
  page: `https://github.com/${REPO}/releases/latest`,
};

let cached = null;

export function useLatestRelease() {
  const [rel, setRel] = useState(cached || FALLBACK);
  useEffect(() => {
    if (cached) return;
    let alive = true;
    fetch(`https://api.github.com/repos/${REPO}/releases/latest`, { headers: { Accept: "application/vnd.github+json" } })
      .then((r) => (r.ok ? r.json() : null))
      .then((j) => {
        if (!j || !alive) return;
        const find = (re) => (j.assets || []).find((a) => re.test(a.name))?.browser_download_url;
        cached = {
          version: String(j.tag_name || "").replace(/^v/, ""),
          exe: find(/^SpotiParty-Setup-[\d.]+\.exe$/) || FALLBACK.exe,
          dmg: find(/^SpotiParty-macos-apple-silicon\.dmg$/) || FALLBACK.dmg,
          intel: find(/^SpotiParty-macos-intel\.dmg$/) || FALLBACK.intel,
          page: j.html_url || FALLBACK.page,
        };
        setRel(cached);
      })
      .catch(() => {});   // offline or rate-limited: the fallback links still work
    return () => { alive = false; };
  }, []);
  return rel;
}
