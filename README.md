# Convert ACM Latex documents to Tufte inspired HTML
This is a work in progress.

## Installation
```bash
brew install jez/formulae/pandoc-sidenote
uv tool install pandoc-tex-numbering
uv tool install git+https://github.com/imandel/tufte-acm-pandoc
```

## Use

Download the default file:
```curl -O https://raw.githubusercontent.com/imandel/tufte-acm-pandoc/main/defaults/tufte-acm.yaml```

then:

```bash
pandoc main.tex \
  --defaults=tufte-acm.yaml \
  --bibliography=your_bib_file.bib \
  -o paper.html
```

## Quirks
You have to change any `\begin{table*}...\end{table*}` to `\begin{table}...\end{table}` to be correctly parsed. You can do that with sed.

```bash
cat *.tex | sed 's/table\*/table/g' | pandoc --defaults=academic-paper.yaml --bibliography=ref.bib -o paper.html
```
