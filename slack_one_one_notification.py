"""Generate a random list of pairs of Bayesians for regular 1:1."""

import collections
import json
import os
from typing import Dict, List, Mapping, Optional, Set, Tuple

# A JSON object with keys managers and values lists of managees, as Slack IDs.
_BAYESIAN_MANAGERS = json.loads(os.getenv('BAYESIAN_MANAGERS', '{}'))


def _prepare_managers() -> Dict[str, Set[str]]:
    forbidden: Dict[str, Set[str]] = collections.defaultdict(set)
    for manager, managees in _BAYESIAN_MANAGERS.items():
        for managee in managees:
            forbidden[manager] |= {managee}
            forbidden[managee] |= {manager}
    return forbidden


_FORBIDDEN_LIST = _prepare_managers()
_BAYESIANS_SLACK_LIST = set(_FORBIDDEN_LIST)


def draw_pairs(
        available: Set[str], *,
        pairs: Optional[Set[Tuple[str, str]]] = None,
        forbidden: Mapping[str, Set[str]]) -> Set[Tuple[str, str]]:
    """Choose a list of Bayesian pairings."""

    if not pairs:
        pairs = set()
    if len(available) <= 1:
        return pairs
    to_pair = next(iter(available))
    for paired_with in available - {to_pair} - forbidden[to_pair]:
        matches = draw_pairs(
            available - {to_pair, paired_with},
            pairs=pairs | {(to_pair, paired_with)}, forbidden=forbidden)
        if matches:
            return matches
    return set()


# TODO(cyrille): Use with airtable data.
def draw_from_oldest(available: Set[str], previous_pairings: List[Tuple[str, str]]) \
        -> Set[Tuple[str, str]]:
    """Try to make a matching, with a least-recently-used policy.

    previous_pairings might be mutated.
    """

    while True:
        forbidden: Dict[str, Set[str]] = collections.defaultdict(set)
        for key, values in _FORBIDDEN_LIST.items():
            forbidden[key] |= values
        for one, two in previous_pairings:
            forbidden[one] |= {two}
            forbidden[two] |= {one}
        match = draw_pairs(available, pairs=set(), forbidden=forbidden)
        if match:
            return match
        previous_pairings.pop(0)


# TODO(cyrille): Use in a Zappa scheduled task instead.
if __name__ == '__main__':
    new_pairs = draw_pairs(_BAYESIANS_SLACK_LIST, forbidden=_FORBIDDEN_LIST)
    print(new_pairs)
