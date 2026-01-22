from sklearn.metrics import roc_auc_score

def evaluate(y_true, y_pred):
    """
    Compute the ROC-AUC (Receiver Operating Characteristic - Area Under the Curve)
    for a set of predictions.

    This is a thin wrapper around ``sklearn.metrics.roc_auc_score`` and should be
    used when you want a single scalar measure of how well the predicted scores
    separate the positive and negative classes.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground truth (correct) target labels or binary indicators.
    y_pred : array-like of shape (n_samples,) or (n_samples, n_classes)
        Predicted scores, probabilities, or decision function values as
        expected by ``roc_auc_score`` (e.g., probability of the positive class
        in the binary case).

    Returns
    -------
    float
        ROC-AUC score, where 1.0 indicates perfect separation and 0.5 indicates
        performance no better than random guessing for balanced binary classes.
    """
    return roc_auc_score(y_true, y_pred)
