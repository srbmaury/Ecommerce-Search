from typing import Sequence
import numpy as np
from sklearn.metrics import roc_auc_score


def evaluate(
    y_true: Sequence,
    y_pred: Sequence,
    *,
    multi_class: str = "ovr",
    average: str = "macro"
) -> float:
    """
    Compute the ROC-AUC score for model predictions.

    This function centralizes ROC-AUC evaluation logic so behavior remains
    consistent across experiments and pipelines.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground-truth binary or multiclass labels.
    y_pred : array-like
        Predicted probabilities or scores. For multiclass problems,
        expected shape is (n_samples, n_classes).
    multi_class : {"ovr", "ovo"}, default="ovr"
        Strategy for multiclass ROC-AUC computation.
    average : {"macro", "weighted", "micro"}, default="macro"
        Averaging strategy for multiclass ROC-AUC.

    Returns
    -------
    float
        ROC-AUC score.

    Raises
    ------
    ValueError
        If ROC-AUC cannot be computed (e.g., only one class present).
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if len(np.unique(y_true)) < 2:
        raise ValueError("ROC-AUC is undefined when only one class is present.")

    return roc_auc_score(
        y_true,
        y_pred,
        multi_class=multi_class if y_pred.ndim > 1 else "raise",
        average=average if y_pred.ndim > 1 else None,
    )
