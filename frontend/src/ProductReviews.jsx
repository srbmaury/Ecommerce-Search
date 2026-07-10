import { useState, useEffect, useCallback, useRef } from 'react';
import { fetchProductReviews, submitProductReview, deleteProductReview } from './api';
import StarRating from './StarRating';

function StarPicker({ value, onChange }) {
    return (
        <div className="star-picker" role="radiogroup" aria-label="Rating">
            {[1, 2, 3, 4, 5].map(n => (
                <button
                    key={n}
                    type="button"
                    role="radio"
                    aria-checked={value === n}
                    aria-label={`${n} star${n > 1 ? 's' : ''}`}
                    className={n <= value ? 'star-picker-btn filled' : 'star-picker-btn'}
                    onClick={() => onChange(n)}
                >
                    ★
                </button>
            ))}
        </div>
    );
}

export default function ProductReviews({ productId, user }) {
    const [reviews, setReviews] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [rating, setRating] = useState(0);
    const [comment, setComment] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState(null);
    const [deleting, setDeleting] = useState(false);

    const loadReviews = useCallback(() => {
        if (!productId) return;
        setLoading(true);
        fetchProductReviews(productId)
            .then(data => {
                setReviews(data.reviews || []);
                setError(null);
            })
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, [productId]);

    useEffect(() => {
        loadReviews();
    }, [loadReviews]);

    // Prefill the form with the user's existing review once it loads, so
    // "Update Review" edits their real rating/comment instead of a blank
    // form silently overwriting it. Only runs while the form is untouched.
    const prefilledRef = useRef(false);
    useEffect(() => {
        if (prefilledRef.current || !user) return;
        const mine = reviews.find(r => r.user_id === user.user_id);
        if (mine) {
            prefilledRef.current = true;
            setRating(mine.rating);
            setComment(mine.comment || '');
        }
    }, [reviews, user]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!rating) {
            setSubmitError('Please select a star rating.');
            return;
        }
        setSubmitting(true);
        setSubmitError(null);
        try {
            await submitProductReview(productId, rating, comment, user.token);
            setRating(0);
            setComment('');
            loadReviews();
        } catch (err) {
            setSubmitError(err.message);
        } finally {
            setSubmitting(false);
        }
    };

    const handleDelete = async () => {
        if (!confirm('Delete your review?')) return;
        setDeleting(true);
        try {
            await deleteProductReview(productId, user.token);
            prefilledRef.current = false;
            setRating(0);
            setComment('');
            loadReviews();
        } catch (err) {
            setSubmitError(err.message);
        } finally {
            setDeleting(false);
        }
    };

    const myReview = user ? reviews.find(r => r.user_id === user.user_id) : null;

    return (
        <div className="product-reviews">
            <h3 className="reviews-heading">Reviews {reviews.length > 0 && `(${reviews.length})`}</h3>

            {user && (
                <form className="review-form" onSubmit={handleSubmit}>
                    <StarPicker value={rating} onChange={setRating} />
                    <textarea
                        className="review-comment-input"
                        placeholder="Share your thoughts about this product (optional)"
                        value={comment}
                        onChange={e => setComment(e.target.value)}
                        maxLength={2000}
                        rows={3}
                    />
                    {submitError && <div className="review-form-error">{submitError}</div>}
                    <div className="review-form-actions">
                        <button type="submit" className="review-submit-btn" disabled={submitting}>
                            {submitting ? 'Submitting...' : myReview ? 'Update Review' : 'Submit Review'}
                        </button>
                        {myReview && (
                            <button
                                type="button"
                                className="review-delete-btn"
                                onClick={handleDelete}
                                disabled={deleting}
                            >
                                {deleting ? 'Deleting...' : 'Delete My Review'}
                            </button>
                        )}
                    </div>
                </form>
            )}

            {loading ? (
                <div className="review-list-loading">Loading reviews...</div>
            ) : error ? (
                <div className="review-list-error">{error}</div>
            ) : reviews.length === 0 ? (
                <div className="review-list-empty">No reviews yet. Be the first to review this product!</div>
            ) : (
                <ul className="review-list">
                    {reviews.map(r => (
                        <li key={r.id} className={r.user_id === user?.user_id ? 'review-item review-item-mine' : 'review-item'}>
                            <div className="review-item-header">
                                <span className="review-item-username">
                                    {r.username}{r.user_id === user?.user_id && ' (you)'}
                                </span>
                                <StarRating rating={r.rating} />
                            </div>
                            {r.comment && <p className="review-item-comment">{r.comment}</p>}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
