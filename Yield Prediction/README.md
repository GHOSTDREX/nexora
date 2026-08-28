# Yield Prediction

Active development module. The observed source datasets are in `dataset/raw/` and the supplied model artifact is in `model/final_yield_prediction_model.pkl`.

The production model service is `backend/app/ml/model_service.py`; the React client is in the repository `frontend/` app. The empty module-local `notebook/` and `src/` directories remain reserved for future research and module-specific code.

Dataset assumptions and validation should be documented before training or deployment. Do not claim predictive accuracy until a reproducible split, evaluation protocol, and field validation are established.
