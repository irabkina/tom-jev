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

## Belief moves action prediction, not goal recognition

Measured over 52 scenarios in four templates, the effect of adding an
agent's belief depends almost entirely on what Jev is asked:

| task family | template | n | mean TV influence | corrections |
|---|---|---|---|---|
| action prediction | attribution | 12 | 0.69 | 9 |
| action prediction | first order | 12 | 0.48 | 6 |
| action prediction | second order | 16 | 0.46 | 8 |
| **goal recognition** | first order | 12 | **0.07** | **1** |

All five failing cells in the corpus are goal recognition. This is not one
bad item: it replicates across `coffee`, `darkroom` and `greenhouse`, three
domains with no shared vocabulary, two of them generated and run once with
no revision.

The mechanism is visible in the distributions. In `darkroom` and
`greenhouse`, P(primary goal) sits at 0.97–1.00 in *every* pass, sparse and
rich alike. Being seen walking to the darkroom carrying exposed film fixes
the goal inference, and neither the objective world state nor the agent's
explicit belief dislodges it. `coffee` is the only goal-recognition domain
where anything moves at all, which is why it looked like an outlier before
the other two existed.

Read alongside the action-prediction results, where the same manipulation
moves 0.46–0.69 and produces 23 corrections with no regressions, the
contrast is the finding rather than a defect:

**An observed action appears to determine goal inference strongly enough
that belief information does not change it. The same belief information
substantially changes predictions of what an agent will do next.**

This reframes `coffee_false_negative`, previously recorded as an open
problem: it is the first observed instance of a systematic effect, not a
broken stimulus. It stays unmodified.

### What would test it

The observation and the belief are confounded in the current design: every
goal-recognition item states an observation that already implies the
primary goal. Two follow-ups would separate them — an item whose observed
action is compatible with several goals equally, and one where belief and
observation point at *different* goals rather than belief merely
subtracting one. Neither exists yet.

### A caution

`influence` and `|utility|` are identical to three decimals at every option
count, including five. Probability never moved between two incorrect
options anywhere in the corpus: answers either move to the correct one or
do not move. The two measures were meant to separate at three or more
options. They have not, and until they do, TV distance is carrying no
information that the signed change does not.
