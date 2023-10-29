Instructions to translate a book:

```
                $ cd world-mother
lives-of-alcyone$ echo "Special terms: buddhic=будхический" > gpt4_context.md
lives-of-alcyone$ ../en2ru.sh -i index.md
```

The same script may be used to improve an existing translation, to fix stylistic and other mistakes in it:

```
                $ cd world-mother
lives-of-alcyone$ ../en2ru.sh -i index.md -p "@ "
```

The `@` prefix will be appended to each processed paragraph.
