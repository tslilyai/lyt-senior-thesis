PAPER = thesis.tex
BASE := $(basename $(PAPER))
EVERYTHING = $(BASE).pdf

OURENV = TEXINPUTS="sty:" 

LATEX = $(OURENV) xelatex -file-line-error -interaction nonstopmode
BIBTEX = bibtex -min-crossrefs=100

main: $(BASE).pdf
all: $(EVERYTHING)

XFIGS := $(wildcard figures/*.fig)
XTABLES := $(wildcard figures/*.tex)
TEXFIGS := $(XFIGS:.fig=.tex)
TEXTABLES := $(XTABLES:.tex=.tex)

TEX := $(wildcard *.tex) $(TEXFIGS) $(TEXTABLES)
BIBS := $(wildcard *.bib)

DEPS := $(TEX) $(BIBS) $(TEXFIGS) $(TEXTABLES)

RERUN = egrep -q '(^LaTeX Warning:|\(natbib\)).* Rerun'
UNDEFINED = egrep -q '^(LaTeX|Package natbib) Warning:.* undefined'
HASCITATION = egrep -q '^(\\citation)'

# HASLATEXMK := $(shell latexmk --version 2>/dev/null)

ifeq ($(HASLATEXMK),)
LATEXRUN = $(LATEX)
%.pdf: %.tex
	$(LATEX) $<
	! $(HASCITATION) $*.log || $(BIBTEX) $*
	! $(UNDEFINED) $*.log || $(LATEX) $<
	! $(UNDEFINED) $*.log || $(BIBTEX) $*
	! $(RERUN) $*.log || $(LATEX) $<
	! $(RERUN) $*.log || $(LATEX) $<
else
LATEXRUN = latexmk -r .latexmkrc
%.pdf: %.tex always
	$(LATEXRUN) -pdf $<
endif

spell:
	@ for i in $(SPELLTEX); do aspell --mode=tex -p ./aspell.words -c $$i; done
	@ for i in $(SPELLTEX); do perl bin/double.pl $$i; done
	@ for i in $(SPELLTEX); do perl bin/abbrv.pl  $$i; done
	@ bash bin/hyphens.sh $(SPELLTEX)
	@ ( head -1 aspell.words ; tail -n +2 aspell.words | sort ) > aspell.words~
	@ mv aspell.words~ aspell.words

clean:
	-rm -rf latex.out
	-rm -f *.aux *.dvi *.log *.blg *.bbl *.bak *.lof *.lot *.toc *.brf *.out *.fls *.fdb* *.ps *.bcf

always:
	@:

.PHONY: clean spell always
