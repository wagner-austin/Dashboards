# Audit: scoring-a-model-you-do-not-ship

Claim-by-claim check of the article against the wiki sentences it derives from,
and of those wiki sentences against their own evidence. Verdicts: `supported`,
`stale`, `overclaim`, `unsourced`, `framing`. Re-run whenever the cited page's
`fact_checked` moves.

Audited 2026-09-14 against API `d89684561`. Source page:
`personal/shipped-checkpoint-and-reported-score-can-be-different-models`
(fact_checked 2026-08-26), private. The training code and its tests are
public.

## Result and facts

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| three ordinary decisions compose into publishing a score for a model that never ships | § The mechanism | `base_trainer_checkpoints.py:60-67` docstring states the same composition | supported |
| the manifest carried a validation loss from epoch 17 beside a test loss measured on epoch 20 | § The measurement | the docstring: "mi-kk-armB-realsplit-seed42 uploaded epoch 17 and reported a test loss measured on epoch 20"; `test_base_trainer_best_checkpoint.py:10` | supported |
| measured, fixed, confirmed on the cluster | § The fix, confirmed on a real run, jobs 55597075 and 55597079 | | supported by the page's job ids; the runs themselves are on the cluster |
| the reported score now describes the uploaded bytes, verified on a run whose best epoch was not the last | same, arm B | `best_checkpoint_restored` logged three seconds before the test line, per the page | supported |
| 0.0011 test loss, in the predicted direction, on one arm | same, the table: 0.8634 before, 0.8623 after | 0.8634 − 0.8623 = 0.0011 | supported |
| PyTorch, GPT-2, Slurm, digest-pinned images | same section | | supported |

## Three correct decisions, one wrong model

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| best-checkpoint save overwrites on every improvement; final save skipped when a best exists; test runs against the resident model | § The mechanism | `base_trainer_checkpoints.py` docstring: "``train`` skips the final save while such a checkpoint exists" | supported |
| the resident model is the last epoch, not the selected one | same | same | supported |
| nothing fails; no error state | § Why the run cannot notice | | supported |

## The test was harder to write than the fix

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| the fix reloads the selected weights before scoring, from disk rather than memory, so a truncated save surfaces at scoring time | § The fix and what it required; the code docstring "Reloading from disk rather than from an in-memory snapshot is deliberate" | `base_trainer_checkpoints.py:68-71`; `reload.py` | supported |
| a uniform corpus drives validation down monotonically: 0.3326, 0.0231, 0.0046, 0.0024 | § The fix and what it required | the page's footnote 2 | supported |
| when the best epoch is the last, the test passes against the defect it exists to catch | same; the test's own comment "the assertion below is vacuous" | `test_base_trainer_best_checkpoint.py:275-277` | supported |
| twelve training lines over thirty epochs; the test asserts its premise and reports itself blind | same | `:221` `"num_epochs": 30`; `:281` "MEMORISES its twelve training lines"; `:290-296` the raise | supported |
| the excerpt | `test_base_trainer_best_checkpoint.py:290-296`, one expression elided and marked | diffed against `d89684561` | supported |

## What it cost, and what that does not prove

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| 0.8634 against 0.8623, 0.0011 too high, the predicted direction | § The fix, confirmed, the table | | supported |
| not attributable to the fix: different environments, conda against the image; no attempt to separate | same, "not attributable to the fix alone" | | supported |
| what is attributable is which model got scored; the restore logged three seconds before the test result | same | | supported |
| both branches exercised in one submission: arm B restores, arm A with no holdout does nothing | same, "That pairing is the useful part" | `test_restore_without_a_holdout_leaves_the_live_model_untouched` covers the second branch in the suite as well | supported |

## Record and Known limits

| claim | wiki sentence | evidence checked | verdict |
|---|---|---|---|
| the page carries job ids, the artifact digest and byte count, and which evidence supports which claim | § Where the evidence for each claim lives | | supported |
| one run each side; the four-decimal agreement is an observation | § The fix, confirmed, the caveat paragraph | | supported |
| the comparability consequence is a reading, not something a manifest records | § Scope | | supported |
| every figure and mechanism claim re-checked against current code 2026-09-14 | this audit | | supported |

## Sources block

Every link probed 200 on 2026-09-14, all at `d89684561`:
`base_trainer_checkpoints.py`, `reload.py`, `test_base_trainer_best_checkpoint.py`,
`test_reload_shipped_weights.py`.
