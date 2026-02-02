// Universal API base URL config for all environments
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || window.location.origin;

export default API_BASE_URL;
