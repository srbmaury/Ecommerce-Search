export const formatPrice = (price) =>
    price?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) ?? '—';

const CATEGORY_COLORS = {
    accessories: '#f97316',
    audio:       '#8b5cf6',
    computers:   '#3b82f6',
    electronics: '#0ea5e9',
    gaming:      '#ef4444',
    networking:  '#06b6d4',
    photography: '#ec4899',
    'smart home':'#10b981',
    storage:     '#f59e0b',
};

const CATEGORY_EMOJIS = {
    accessories: '🎒',
    audio:       '🎧',
    computers:   '💻',
    electronics: '⚡',
    gaming:      '🎮',
    networking:  '🌐',
    photography: '📷',
    'smart home':'🏠',
    storage:     '💾',
};

export function getCategoryColor(category) {
    if (!category) return '#6366f1';
    return CATEGORY_COLORS[category.toLowerCase()] ?? '#6366f1';
}

export function getCategoryEmoji(category) {
    if (!category) return '🛍️';
    return CATEGORY_EMOJIS[category.toLowerCase()] ?? '🛍️';
}
