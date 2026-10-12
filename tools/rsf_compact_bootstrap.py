"""Omite filas de peso cero de cada bootstrap, conservando muestras y pesos."""
import numpy as np
from sklearn.base import clone
from sklearn.ensemble._forest import _generate_sample_indices
import sksurv.ensemble.forest as implementation

ORIGINAL = implementation._parallel_build_trees
CHECKS = []


def compact(tree, bootstrap, X, y, sample_weight, tree_idx, n_trees,
            verbose=0, class_weight=None, n_samples_bootstrap=None,
            missing_values_in_feature_mask=None):
    if not bootstrap or sample_weight is not None or class_weight is not None:
        return ORIGINAL(tree, bootstrap, X, y, sample_weight, tree_idx, n_trees,
                        verbose, class_weight, n_samples_bootstrap, missing_values_in_feature_mask)
    indices = _generate_sample_indices(tree.random_state, X.shape[0], n_samples_bootstrap, None)
    selected, counts = np.unique(indices, return_counts=True)
    data = X[selected].tocsc()
    data.sort_indices()
    target = (y[0][selected], y[1], y[2])
    reference = clone(tree) if tree_idx == 0 else None
    tree._fit(data, target, sample_weight=counts, check_input=False,
              missing_values_in_feature_mask=missing_values_in_feature_mask)
    if reference is not None:
        ORIGINAL(reference, bootstrap, X, y, sample_weight, tree_idx, n_trees,
                 verbose, class_weight, n_samples_bootstrap, missing_values_in_feature_mask)
        same = all(np.array_equal(getattr(tree.tree_, field), getattr(reference.tree_, field))
                   for field in ['feature', 'threshold', 'children_left', 'children_right'])
        delta = float(np.max(abs(tree.tree_.value-reference.tree_.value))) if same else None
        check = {'outcome':'pass' if same and delta < 1e-10 else 'fail',
                 'same_splits':same,'maximum_curve_difference':delta,
                 'full_training_rows':X.shape[0],'bootstrap_draws':int(n_samples_bootstrap),
                 'nonzero_weight_rows':len(selected)}
        CHECKS.append(check)
        if check['outcome'] != 'pass':
            raise RuntimeError('La compactacion bootstrap no reproduce el arbol de referencia.')
    return tree


def enable():
    implementation._parallel_build_trees = compact
