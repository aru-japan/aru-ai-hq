"""Source taxonomy for ARu Intelligence Phase 2 -- Source Library expansion.

Two flat lists, mirroring life_topics.py's shape:
  SOURCE_CATEGORIES        -- what domain a monitored source belongs to
  UPDATE_CLASSIFICATIONS   -- what kind of change a detected update represents

Both are single sources of truth: ensure_schema() in source_watcher.py reads
them to build the Select option lists, and classify_update() reads
UPDATE_CLASSIFICATIONS to validate the AI's output against a known set
(hallucinated labels are dropped/replaced, never saved as-is).
"""

SOURCE_CATEGORIES = [
    "Immigration",
    "Visa",
    "Student",
    "Employment",
    "Tax",
    "Pension",
    "Health Insurance",
    "Disaster",
    "Transportation",
    "Tourism",
    "Events",
    "Festivals",
    "Municipal Governments",
    "Universities",
    "Japanese Language Schools",
    "Weather",
    "Culture",
    "Consumer Information",
    "Housing",
    "Banking",
    "Emergency",
    "Trending Topics",
]

# Categories where a detected change is inherently high-stakes regardless of a
# given source's individually-set Importance -- used only as a sensible default
# suggestion, never to silently override an editor's explicit Importance choice.
CRITICAL_DEFAULT_CATEGORIES = {"Immigration", "Visa", "Tax", "Health Insurance", "Disaster", "Emergency"}

UPDATE_CLASSIFICATIONS = [
    "Law Change",
    "Policy Update",
    "Fee Change",
    "Deadline Change",
    "Event Update",
    "Festival Schedule",
    "Weather Warning",
    "Transportation",
    "Tourism Information",
    "Emergency Notice",
    "General News",
]
