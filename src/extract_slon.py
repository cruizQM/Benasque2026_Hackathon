#code/Not_Noisy/MaxCut/PCE_CUNQA/src/extract_slon.py
def select_min_loss_candidates(experiment_result):
    """
    Return all candidates whose loss equals the minimum loss found in
    the optimization history.

    Parameters
    ----------
    experiment_result : list[dict]
        List of records produced during the optimization process.
        Each record must contain at least the key "loss".

    Returns
    -------
    list[dict]
        All records achieving the minimum loss.

    Raises
    ------
    ValueError
        If experiment_result is empty or malformed.
    """
    if not experiment_result:
        raise ValueError("experiment_result is empty; cannot select candidates.")

    try:
        min_loss = min(entry["loss"] for entry in experiment_result)
    except KeyError as exc:
        raise ValueError("Each experiment_result entry must contain a 'loss' key.") from exc

    best_candidates = [entry for entry in experiment_result if entry["loss"] == min_loss]

    if not best_candidates:
        raise ValueError("No candidates found with the minimum loss.")

    return best_candidates