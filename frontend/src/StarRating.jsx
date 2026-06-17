export default function StarRating({ rating }) {
    const filled = Math.round(rating || 0);
    return (
        <div className="pc-stars">
            {Array.from({ length: 5 }, (_, i) => (
                <span key={i} className={i < filled ? 'star filled' : 'star'}>★</span>
            ))}
            <span className="pc-rating-text">{rating?.toFixed(1)}</span>
        </div>
    );
}
