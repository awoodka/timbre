"""Does the space encode *emotional* kinship (mood/arc), across genre?

Uses RELATIVE structure (cohesion vs. separation, ordered triplets) rather than
brittle absolute top-k. Ground truth + sources: tests/_helpers.py.
"""

import pytest

from tests._helpers import (
    CLUSTERS, mean_within_sim, mean_cross_sim, sim, present,
)

# Clusters whose emotional opposite is clearly the cozy/uplifting cluster.
_DARK_CLUSTERS = ["devastation", "cosmic_dread", "melancholy_longing", "oppressive_dystopia"]


@pytest.mark.parametrize("cluster", list(CLUSTERS))
def test_cluster_is_internally_cohesive(corpus, cluster):
    """Books sharing a mood should, on average, be more similar to each other
    than to the corpus at large."""
    within = mean_within_sim(corpus, CLUSTERS[cluster])
    # baseline: average similarity of cluster members to all other books
    members = set(present(corpus, CLUSTERS[cluster]))
    others = [t for t in corpus if t not in members]
    baseline = mean_cross_sim(corpus, list(members), others)
    assert within > baseline + 0.05, (
        f"Cluster '{cluster}' not cohesive: within={within:.3f} vs baseline={baseline:.3f}. "
        f"Members may be scattered across the space."
    )


@pytest.mark.parametrize("dark", _DARK_CLUSTERS)
def test_dark_clusters_separate_from_cozy_uplifting(corpus, dark):
    """A dark mood cluster should be internally tighter than its similarity to
    the emotional-opposite cozy/uplifting cluster."""
    within = mean_within_sim(corpus, CLUSTERS[dark])
    cross = mean_cross_sim(corpus, CLUSTERS[dark], CLUSTERS["cozy_uplifting"])
    assert within > cross, (
        f"'{dark}' not separated from cozy/uplifting: within={within:.3f} <= cross={cross:.3f}"
    )
    assert cross < 0.25, (
        f"'{dark}' is too similar to cozy/uplifting (cross={cross:.3f}); emotional "
        "opposites should be near-orthogonal."
    )


# (anchor, closer, farther, why) — emotion over genre. Sourced groupings.
ORDERED_TRIPLETS = [
    ("The Road", "A Little Life", "The Hobbit",
     "post-apoc & contemporary share devastation; cozy adventure is opposite"),
    ("Never Let Me Go", "Norwegian Wood", "Project Hail Mary",
     "literary-scifi quiet grief closer to literary melancholy than to upbeat space-scifi"),
    ("Annihilation", "House of Leaves", "The House in the Cerulean Sea",
     "cosmic dread (scifi vs experimental horror) over cozy warmth"),
    ("Blood Meridian", "The Road", "The Hitchhiker's Guide to the Galaxy",
     "bleak violence closer to bleak post-apoc than to absurd comedy"),
    ("The House in the Cerulean Sea", "The Hobbit", "Blood Meridian",
     "cozy warmth (contemporary fantasy vs classic fantasy) over nihilistic violence"),
    ("1984", "The Handmaid's Tale", "The Hobbit",
     "oppressive dystopias cohere; cozy adventure is opposite"),
]


@pytest.mark.parametrize("anchor,closer,farther,why", ORDERED_TRIPLETS)
def test_emotional_ordering_beats_genre(corpus, anchor, closer, farther, why):
    s_close = sim(corpus, anchor, closer)
    s_far = sim(corpus, anchor, farther)
    assert s_close > s_far, (
        f"{anchor}: expected closer to '{closer}' ({s_close:.3f}) than '{farther}' "
        f"({s_far:.3f}). {why}."
    )


# Subtle / adversarial cases targeting suspected weak spots (sourced). These are
# the ones most likely to FAIL and reveal mis-scoring — that's their job.
SUBTLE_TRIPLETS = [
    ("No Longer Human", "Norwegian Wood", "Rebecca",
     "sources group No Longer Human with Norwegian Wood (alienated melancholy), "
     "not with gothic dread — if this fails, NLH is over-scored on dread"),
    ("No Longer Human", "The Bell Jar", "The Haunting of Hill House",
     "despair/alienation memoirs over haunted-house dread"),
    ("Never Let Me Go", "Klara and the Sun", "Gone Girl",
     "Ishiguro's quiet melancholic sci-fi over a psychological thriller"),
    ("The Year of Magical Thinking", "A Little Life", "Catch-22",
     "grief memoir nearer a grief novel than a war satire"),
    ("Beloved", "The Things They Carried", "Fahrenheit 451",
     "historical grief/trauma nearer war grief than a dystopia"),
]


@pytest.mark.parametrize("anchor,closer,farther,why", SUBTLE_TRIPLETS)
def test_subtle_emotional_ordering(corpus, anchor, closer, farther, why):
    for t in (anchor, closer, farther):
        if t not in corpus:
            pytest.skip(f"{t} not in corpus")
    s_close = sim(corpus, anchor, closer)
    s_far = sim(corpus, anchor, farther)
    assert s_close > s_far, (
        f"{anchor}: expected closer to '{closer}' ({s_close:.3f}) than '{farther}' "
        f"({s_far:.3f}). {why}."
    )


def test_no_emotional_orphans(corpus):
    """Every book should have at least one genuine neighbor. A book whose best
    match is very weak is usually a scoring outlier (wrong dominant emotions)."""
    weak = {}
    for t in corpus:
        best = max(sim(corpus, t, o) for o in corpus if o != t)
        if best < 0.32:
            weak[t] = round(best, 2)
    assert not weak, (
        f"Books with no meaningful nearest neighbor (likely mis-scored): {weak}"
    )
