The canonical source describes what a page means: its role, title, narrative,
artwork provenance, and place in the issue. It does not require an author to
write renderer-specific markup.

This separation makes review ordinary. A title change is a small JSON diff. A
paragraph revision is a small Markdown diff. A theme update does not rewrite
the story.

Three principles keep the source durable:

- stable identifiers survive layout changes;
- page order is explicit rather than inferred;
- generated PDF and HTML never become canonical.

The renderer can evolve while the edition remains recognizable.
