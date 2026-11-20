"""buoc.dau (bước đầu, "first step"): text counting that understands Vietnamese, Chinese, Japanese and Korean."""
from ._version import __version__
from .counter import Counts, analyse, load_lexicon, normalise, segment

__all__ = ["Counts", "__version__", "analyse", "load_lexicon", "normalise", "segment"]
