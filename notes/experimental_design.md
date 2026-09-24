# Experimental design

## Symmetric action alternatives

Early pilot scenarios framed action prediction as a binary choice between an affirmative action and its negation (e.g., `go_to_office` vs. `do_not_go_to_office`). This design produced a strong affirmative-action bias: Jev assigned very high probability to the goal-consistent affirmative action across world states. As a result, adding an explicit positive belief often had almost no effect, while explicit negative beliefs sometimes substantially reduced the probability of the affirmative action.

This asymmetry obscured the intended manipulation. In particular, scenarios annotated as requiring explicit belief representation did not reliably show greater representational influence than control scenarios.

Replacing **A vs. not-A** choices with **symmetric competing actions (A vs. B)** resolved the issue. For the report-location task, Jev chooses between two plausible destinations (e.g., `go_to_office` vs. `go_to_conference_room`). Objective world state favors one destination, while the agent's represented belief may favor the same or the alternative destination.

Under this design:

* When belief and reality agree, Sparse and Rich representations produce nearly identical distributions (TV influence 0.00–0.04).
* When belief and reality conflict, adding the explicit belief produces large distributional shifts (TV influence 0.84–0.96).
* In both conflict directions, the Rich representation corrects the Sparse prediction.
* The earlier positive-vs.-negative belief asymmetry disappears.

### Design implication

For experiments testing the effect of re-representation on Jev decisions, prefer **symmetric competing alternatives (A vs. B)** over **an action and its negation (A vs. not-A)**.

A vs. not-A can introduce a strong default toward the concrete, goal-consistent affirmative action, making representational effects difficult to interpret. A vs. B provides competing positive actions and allows belief information to shift probability mass between comparably structured alternatives.

The original A vs. not-A results should be retained as a methodological pilot rather than treated as evidence against the re-representation hypothesis.

## Not tuning stimuli to results

`coffee_false_negative` is the one failing cell in the corpus: annotated as
requiring belief, it measures influence ~0.05 where its group averages 0.80,
and the rich pass still answers `get_coffee` despite Sam believing there is
none. It is left as it is, deliberately.

Revising a scenario until it produces the expected measurement is fitting the
stimulus to the hypothesis. The measurement stops being evidence at that
point — a corpus tuned until every cell behaves is guaranteed to behave, and
says nothing.

This matters beyond that one cell, because parts of the corpus were revised in
response to measurements:

| set | history | independent? |
|---|---|---|
| `coffee` | rebuilt three times after seeing results: A vs. not-A, then two destinations, then goal recognition with three goals and affordances | no |
| `report` | options changed from A vs. not-A to two destinations after observing the affirmative bias | no |
| `meeting` | written once, worked first run | **yes** |
| `attribution` | written once, worked first run | **yes** |

The corpus-level separation — influence 0.80 where belief is annotated
relevant against 0.03 where it is not — is therefore not all independent
evidence. `meeting` and `attribution` are, having never been revised against
their own results. `coffee` and `report` should be read as the pilot that
established the A vs. B design rule, not as confirmation of the hypothesis
they were reshaped under.

The distinction worth preserving in future work: changing a scenario because
its *construction* is wrong — a missing precondition, an option with no
affordance, an incoherent ground truth — is fixing a bug. Changing it because
the *result* is wrong is overfitting. The first is legitimate at any time; the
second invalidates the item as evidence.
