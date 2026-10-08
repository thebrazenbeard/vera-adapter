# Training-derived portable Vera invariants v1

Source examined: `thebrazenbeard/vera_model_training` on its live `main` state during extraction.

## Promoted into the adapter

1. **Source-bounded truth.** Durable state carries provenance; recollection or generated text does not become live truth merely by appearing in model output.
2. **Supersession.** A later explicit correction replaces an earlier value for the same continuity key.
3. **Exactness requires backing.** Exact identifiers, numbers, tokens, and similar claims are withheld when their backing record is unavailable.
4. **Qualification separation.** Training/proxy success is evidence about a package, not proof that a different native model is qualified.
5. **Effect separation.** The adapter may propose cognition/actions, but host authorization remains separate from execution.
6. **Provider neutrality.** Identity/continuity is represented independently of the model/provider used for a turn.

## Deliberately not copied

- GGUF/llama.cpp bootcamp implementation and zero-cost GitHub-runner constraints.
- Trainer/Student/Examiner mechanics.
- Provider/model names and prompt-specific behavior.
- Public-repository privacy assumptions as a runtime identity mechanism.
- Claims that proxy scores transfer into a native model.
- Historical checkpoint state as current Vera state.

## Evidence boundary

This extraction is SOURCE_INSPECTION plus implementation work. It is not a native qualification, real-system runtime probe, deployment, or formal verification. The training repository remains source material; current runtime/project authority must still be resolved independently.
