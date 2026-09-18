# Writing-style research

The skill uses a local synthesis called **Literate Engineering Voice**. It is not a claim that one external guide defines the whole style.

## Sources

- Microsoft Writing Style Guide — “Above all, simple and human”:
  https://learn.microsoft.com/en-us/style-guide/brand-voice-above-all-simple-human
  - favors warm, relaxed, crisp, clear language;
  - puts the important point first;
  - recommends ordinary words and removing excess wording.

- Google Technical Writing — Active voice:
  https://developers.google.com/tech-writing/one/active-voice
  - prefers active voice because it identifies the actor and usually reads more directly.

- Google Technical Writing — Clear sentences:
  https://developers.google.com/tech-writing/one/clear-sentences
  - prioritizes clarity, strong verbs, and concrete subjects.

- Google Technical Writing One summary:
  https://developers.google.com/tech-writing/course-summaries/one
  - recommends consistent terms, specific nouns, one idea per sentence, concise wording, and peer feedback.

- Diátaxis:
  https://diataxis.fr/
  - separates tutorial, how-to, reference, and explanation needs instead of mixing them into one undifferentiated document.

## Local synthesis

For literate source, prose is neither a tutorial nor decorative commentary. Its first job is to explain the implementation's problem, invariant, ownership, and surprising constraints beside the code.

Long-form teaching belongs downstream in a book/tutorial. API details belong in reference material. Operational recipes belong in how-to docs.

This keeps canonical Org source readable without turning every source file into a chapter or every chapter into an API dump.
