const API_BASE_URL = (() => {
    const host = window.location.hostname;

    if (host === "localhost" || host === "127.0.0.1") {
        return "http://localhost:5000";
    }

    // GitHub Codespaces
    if (host.endsWith(".app.github.dev")) {
        return window.location.origin.replace("-5500.", "-5000.");
    }

    return window.location.origin;
})();
