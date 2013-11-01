Programming Style Guide
-----------------------

A quick note: Throughout development my programming style changed somewhat, so you will see code that does not follow the rules below. All new code obeys these rules.

* Use tabs for line indents. Spaces can be used AFTER tabs to help improve readability or for stylistic reasons.
* Variable names should be prefixed with an underscore (`_chunk_key`) if they are defined outside of a `for` loop. Variables used to iterate through lists/are created in the for loop's definition should omit the underscore. Arguments should never start with an underscore.