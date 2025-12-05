// static/js/theme.js
const STORAGE_KEY = "sahayak_theme_pref";

export function initThemeToggle(toggleSelector = "#theme-toggle") {
  const btn = document.querySelector(toggleSelector);
  if (!btn) return;

  // initial state from localStorage or system

  const saved = localStorage.getItem(STORAGE_KEY);
  let useDark;
  if (saved !== null) useDark = saved === "dark";
  else
    useDark =
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches;

  setDark(useDark);

  btn.addEventListener("click", () => {
    const now = document.body.classList.toggle("dark");
    localStorage.setItem(STORAGE_KEY, now ? "dark" : "light");
  });
}

export function setDark(enabled) {
  if (enabled) document.body.classList.add("dark");
  else document.body.classList.remove("dark");
}

export function initThemeToggle(selector) {
    const btn = document.querySelector(selector);

    btn.addEventListener("click", () => {
        document.body.classList.toggle("dark");

        // fix chat area
        document.getElementById("chat-history").style.backgroundColor =
            document.body.classList.contains("dark")
                ? "#0f172a"
                : "#f5f5f5";
    });
}
