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
