// API utility for recommendations
export async function fetchRecommendations(userId) {
    const res = await fetch(`/api/recommendations?user_id=${userId}`);
    if (!res.ok) throw new Error('Failed to fetch recommendations');
    return res.json();
}
