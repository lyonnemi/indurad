import pathlib
from enum import Enum, StrEnum


class Side(StrEnum):
    LEFT = "L"
    RIGHT = "R"

    def opposite(self) -> "Side":
        return Side.RIGHT if self is Side.LEFT else Side.LEFT


latex_template_path = pathlib.Path(__file__).parent
logo_path = (latex_template_path / "indurad-logo.pdf").absolute()
disclaimer = (latex_template_path / "disclaimer").read_text()
title = "101"


def html(color: str) -> str:
    return r"{HTML}{" + color + r"}"


def font(font_size: int, line_height: int) -> str:
    return r"\fontsize{" f"{font_size}" r"}{" rf"{line_height}" "}"


class Colors(Enum):
    iBlack = "252226"
    iBlack75 = "535358"
    iGold = "b28158"
    iGold80 = "c09670"
    iGold60 = "ceac8d"
    iGold25 = "eadaca"
    iBronze = "cb5161"
    iPortTurquoise = "40a8b5"
    black = "000000"
    black80 = "333333"
    black50 = "808080"
    black10 = "e5e5e5"
    white = "ffffff"

    @property
    def html(self) -> str:
        """Returns the Latex code for the color"""
        return html(self.value)


# Admonition coloring → diverges from indurad color scheme
admonitionOrange = html("f0b37e")
admonitionLightOrange = html("fcefe5")
admonitionLightiBronze = html("f4dcdf")
admonitionLightiGold60 = html("f5eee8")
admonitionLightiPortTurquoise = html("d8edf0")

# We create the following groups of admonition types:
# danger = error
# attention = caution = warning
# hint = important = tip
# note = seealso = todo

colorDanger = Colors.iBronze.html
colorAttention = admonitionOrange
colorHint = Colors.iGold60.html
colorNote = Colors.iPortTurquoise.html

colorDangerBackground = admonitionLightiBronze
colorAttentionBackground = admonitionLightOrange
colorHintBackground = admonitionLightiGold60
colorNoteBackground = admonitionLightiPortTurquoise

iDocumentTitleFontSize = font(36, 39)
iH1HeadlineFontSize = font(24, 28)
iH2HeadlineFontSize = font(18, 22)
iH3HeadlineFontSize = font(14, 17)
iH4HeadlineFontSize = font(12, 15)
iSubheaderFontSize = font(12, 18)
iTextFontSize = font(10, 16)
iHeaderFooterFontSize = font(8, 12)


def escape_characters(text: str) -> str:
    """
    Escapes characters in a given string so that it can be used inside LaTeX
    """
    for char in r"\&%$#_{}~^":
        text = text.replace(char, f"\\{char}")
    return text


def get_latex_elements(
    email: str,
    document_version: str,
    watermark_text: str,
    watermark_scale: float,
    kicker: str,
    subheading: str,
    solution_logo_path_strs: tuple[str, ...],
    insert_disclaimer: bool,
    chapterstart: str,
    even_page_num_pos: Side,
    odd_page_num_pos: Side,
) -> dict[str, str]:
    """
    Returns LaTeX config for Sphinx
    @param email: email that is to be used in the document
    @param document_version: the version to be shown on the title page
    @param watermark_text: text that is shown as watermark
    @param watermark_scale: size of the watermark
    @param kicker: the text that is shown above the title
    @param subheading: the text that is shown directly below the title
    @param solution_logo_path_strs: paths to the logos shown below the title
    @param insert_disclaimer: switch to toggle disclaimer on/off
    @return: `latex_elements` as defined in https://www.sphinx-doc.org/en/master/latex.html
    """
    email = escape_characters(email)
    email_footer = r"~\textbar~\color{iBlack}\href{mailto:" + email + r"}{" + email + r"}%" if email else ""
    document_version = escape_characters(document_version)
    watermark_text = escape_characters(watermark_text).replace("\n", r"\\")
    kicker = escape_characters(kicker)
    subheading = escape_characters(subheading)
    solution_logo_paths = [
        pathlib.Path(solution_logo_path_str).absolute() for solution_logo_path_str in solution_logo_path_strs
    ]
    for solution_logo_path in solution_logo_paths:
        if not solution_logo_path.exists():
            raise FileNotFoundError(f"Path '{solution_logo_path}' specified by option `logo_paths` does not exist.")

    # fmt: off
    return {
        "preamble":
        # define math style
        r"""
        \usepackage[math-style=literal]{unicode-math}
        \usepackage{ragged2e}
        """
        # Combo font for unicode characters in roboto
        r"""
        \usepackage{verbatim}
        \usepackage{combofont}
        % Define a combofont for every font in the family

        % set up roboto

        \setupcombofont{roboto-symbola-regular}{
          {Roboto:\combodefaultfeat} at #1pt,
          {Symbola:\combodefaultfeat} at #1pt
        }{
          {},
          fallback
        }

        \setupcombofont{roboto-symbola-bold}{
          {Roboto/B:\combodefaultfeat} at #1pt,
          {Symbola:\combodefaultfeat} at #1pt
        }{
          {},
          fallback
        }

        \setupcombofont{roboto-symbola-italic}{
          {Roboto/I:\combodefaultfeat} at #1pt,
          {Symbola:\combodefaultfeat} at #1pt
        }{
          {},
          fallback
        }

        \setupcombofont{roboto-symbola-bolditalic}{
          {Roboto/BI:\combodefaultfeat} at #1pt,
          {Symbola:\combodefaultfeat} at #1pt
        }{
          {},
          fallback
        }

        % Now set up the family
        \DeclareFontFamily{TU}{roboto-symbola}{}
        \DeclareFontShape{TU}{roboto-symbola}{m}{n} {<->combo*roboto-symbola-regular}{}
        \DeclareFontShape{TU}{roboto-symbola}{b}{n} {<->combo*roboto-symbola-bold}{}
        \DeclareFontShape{TU}{roboto-symbola}{m}{it} {<->combo*roboto-symbola-italic}{}
        \DeclareFontShape{TU}{roboto-symbola}{b}{it} {<->combo*roboto-symbola-bolditalic}{}

        % since roboto has no smallcaps font, just use normal font
        \DeclareFontShape{TU}{roboto-symbola}{m}{sc} {<->combo*roboto-symbola-regular}{}
        \renewcommand \rmdefault {roboto-symbola}

        % set up roboto condensed

        \setupcombofont{robotocondensed-symbola-regular}{
          {Roboto Condensed:\combodefaultfeat} at #1pt,
          {Symbola:\combodefaultfeat} at #1pt
        }{
          {},
          fallback
        }

        \setupcombofont{robotocondensed-symbola-bold}{
          {Roboto Condensed/B:\combodefaultfeat} at #1pt,
          {Symbola:\combodefaultfeat} at #1pt
        }{
          {},
          fallback
        }

        \setupcombofont{robotocondensed-symbola-italic}{
          {Roboto Condensed/I:\combodefaultfeat} at #1pt,
          {Symbola:\combodefaultfeat} at #1pt
        }{
          {},
          fallback
        }

        \setupcombofont{robotocondensed-symbola-bolditalic}{
          {Roboto Condensed/BI:\combodefaultfeat} at #1pt,
          {Symbola:\combodefaultfeat} at #1pt
        }{
          {},
          fallback
        }

        % Now set up the family
        \DeclareFontFamily{TU}{robotocondensed-symbola}{}
        \DeclareFontShape{TU}{robotocondensed-symbola}{m}{n} {<->combo*robotocondensed-symbola-regular}{}
        \DeclareFontShape{TU}{robotocondensed-symbola}{b}{n} {<->combo*robotocondensed-symbola-bold}{}
        \DeclareFontShape{TU}{robotocondensed-symbola}{m}{it} {<->combo*robotocondensed-symbola-italic}{}
        \DeclareFontShape{TU}{robotocondensed-symbola}{b}{it} {<->combo*robotocondensed-symbola-bolditalic}{}

        \renewcommand \sfdefault {robotocondensed-symbola}
        """
        # Watermark
        r"""
        \usepackage{draftwatermark}
        \SetWatermarkText{""" + watermark_text + r"""}
        \SetWatermarkScale{ """ + str(watermark_scale) + r""" }
        """
        # Chapter/Section Title Style
        r"""
        \usepackage{titlesec}
        \titleformat{\chapter}
          {\normalfont\sffamily""" + iH1HeadlineFontSize + r"""\bfseries\color{iBlack}}
          {\thechapter}{10pt}{}
        \titleformat{\section}
          {\normalfont\sffamily""" + iH2HeadlineFontSize + r"""\bfseries\color{iBlack}}
          {\thesection}{7.5pt}{}
        \titleformat{\subsection}
          {\normalfont\sffamily""" + iH3HeadlineFontSize + r"""\bfseries\color{iBlack}}
          {\thesubsection}{5.9pt}{}
        \titleformat{\subsubsection}
          {\normalfont\sffamily""" + iH4HeadlineFontSize + r"""\bfseries\color{iBlack}}
          {\thesubsubsection}{5pt}{}
        """
        # fncyhdr topmargin
        r"""
        \setlength{\headheight}{26.36232pt}
        \addtolength{\topmargin}{-14.36232pt}
        """
        # support appending pdfs
        r"""
        \usepackage{pdfpages}
        """
        # for the title page
        r"""
        \RequirePackage{tikz}
        \usetikzlibrary{calc}
        \usepackage{tabularx}
        """
        # remove errors because of list depth
        r"""
        \usepackage{enumitem}
        \setlistdepth{9}

        \setlist[itemize,1]{label=$\bullet$}
        \setlist[itemize,2]{label=$\bullet$}
        \setlist[itemize,3]{label=$\bullet$}
        \setlist[itemize,4]{label=$\bullet$}
        \setlist[itemize,5]{label=$\bullet$}
        \setlist[itemize,6]{label=$\bullet$}
        \setlist[itemize,7]{label=$\bullet$}
        \setlist[itemize,8]{label=$\bullet$}
        \setlist[itemize,9]{label=$\bullet$}

        \renewlist{itemize}{itemize}{9}
        """
        # Fix table of contents overlapping.
        r"""
        \usepackage{tocloft}
        \setlength{\cftchapnumwidth}{2em}
        \setlength{\cftsecnumwidth}{3.5em}
        \setlength{\cftsubsecnumwidth}{3.5em}
        \renewcommand{\sphinxtableofcontentshook}{}
        """
        # re-style text blocks
        # https://texdoc.org/serve/tcolorbox.pdf/0
        r"""
        \usepackage[xparse,skins,breakable]{tcolorbox}
        \usepackage{array,tabularx}
        \usepackage{colortbl}
        \usepackage{tcolorbox}
        \DeclareTColorBox{customnotebox}{ m m m m m}
            { colback={#3},coltitle={#4},colframe={#5},
              center,width=1\linewidth,enhanced,fonttitle=\large\bfseries,
              drop fuzzy shadow,breakable,adjusted title={#1},
              halign=left,
              sharpish corners,
              drop shadow,
              rightrule=0mm, leftrule=0mm, bottomrule=0mm,
              before skip=0.5cm,after skip=0.5cm,
              before upper={ \vskip -0.8cm\hfill%
                            #2
                            \vskip +0.5cm\vfill%
                            \small%
                          }
            }

        \renewenvironment{sphinxattention}[1]
            {\begin{customnotebox}{#1}{⚠}{colorAttentionBackground}{white}{colorAttention}}
            {\end{customnotebox}}
        \renewenvironment{sphinxcaution}[1]
            {\begin{customnotebox}{#1}{⚠}{colorAttentionBackground}{white}{colorAttention}}
            {\end{customnotebox}}
        \renewenvironment{sphinxwarning}[1]
            {\begin{customnotebox}{#1}{⚠}{colorAttentionBackground}{white}{colorAttention}}
            {\end{customnotebox}}

        \renewenvironment{sphinxdanger}[1]
            {\begin{customnotebox}{#1}{⚠}{colorDangerBackground}{white}{colorDanger}}
            {\end{customnotebox}}
        \renewenvironment{sphinxerror}[1]
            {\begin{customnotebox}{#1}{⚠}{colorDangerBackground}{white}{colorDanger}}
            {\end{customnotebox}}

        \renewenvironment{sphinxhint}[1]
            {\begin{customnotebox}{#1}{🛈}{colorHintBackground}{white}{colorHint}}
            {\end{customnotebox}}
        \renewenvironment{sphinximportant}[1]
            {\begin{customnotebox}{#1}{🛈}{colorHintBackground}{white}{colorHint}}
            {\end{customnotebox}}
        \renewenvironment{sphinxtip}[1]
            {\begin{customnotebox}{#1}{🛈}{colorHintBackground}{white}{colorHint}}
            {\end{customnotebox}}

        \renewenvironment{sphinxnote}[1]
            {\begin{customnotebox}{#1}{🛈}{colorNoteBackground}{white}{colorNote}}
            {\end{customnotebox}}
        \renewenvironment{sphinxseealso}[1]
            {\begin{customnotebox}{#1}{🛈}{colorNoteBackground}{white}{colorNote}}
            {\end{customnotebox}}
        """
        # redefine enumeration style for numbered lists
        # TODO: doesn't work yet
        # r"""
        # \renewcommand{\labelenumi}{\arabic{enumi}}
        # \renewcommand{\labelenumii}{\arabic{enumi}.\arabic{enumii}}
        # \renewcommand{\labelenumiii}{\arabic{enumi}.\arabi{enumii}.\arabic{enumiii}}
        # \renewcommand{\labelenumiv}{\arabic{enumi}.\arabic{enumii}.\arabic{enumiii}.\arabic{enumiv}}
        # """
        # define colors
        r"""
        \RequirePackage{xcolor}
        """ + "\n".join(rf"\definecolor{{{color.name}}}{color.html}" for color in Colors) + r"""

        \definecolor{colorAttention}""" + colorAttention + r"""
        \definecolor{colorAttentionBackground}""" + colorAttentionBackground + r"""
        \definecolor{colorDanger}""" + colorDanger + r"""
        \definecolor{colorDangerBackground}""" + colorDangerBackground + r"""
        \definecolor{colorHint}""" + colorHint + r"""
        \definecolor{colorHintBackground}""" + colorHintBackground + r"""
        \definecolor{colorNote}""" + colorNote + r"""
        \definecolor{colorNoteBackground}""" + colorNoteBackground +
        # fix space after table caption
        r"""
        \renewcommand\sphinxaftertopcaption{%
          \vspace*{-.2cm}%
        }
        """
        # fix counting of figures and tables
        r"""
        \counterwithout{figure}{chapter}
        \counterwithout{table}{chapter}
        """
        # Re-define \sphinxincludegraphics to center images
        r"""
        \usepackage{graphicx}
        \renewcommand{\sphinxincludegraphics}[2][]{%
            \hbox to \linewidth{\hfil\sphinxsafeincludegraphics[#1]{#2}\hfil}%
        }
        """
        # Allow latex to break lines at hyphens
        r"""
        \renewcommand{\sphinxhyphen}{-\allowbreak}
        """
        # define the header and footer
        r"""
        \makeatletter
          \fancypagestyle{normal}{
            \fancyhf{}
            \renewcommand{\headrulewidth}{1pt}
            \renewcommand{\footrulewidth}{1pt}
            \fancyhead[""" + even_page_num_pos.opposite()
            + r"""E,""" + odd_page_num_pos.opposite() + r"""O]{%
            \color{iGold}\nouppercase{\leftmark}%
            }
            \fancyhead[""" + even_page_num_pos + r"""E,""" + odd_page_num_pos + r"""O]{%
                \includegraphics[height=0.8cm]{""" + str(logo_path) + r"""}%
            }
            \fancyfoot[""" + even_page_num_pos.opposite()
            + r"""E,""" + odd_page_num_pos.opposite() + r"""O]{%
                \color{iBronze}Confidential Copy: Partners/End Users\\%
                \color{iBlack}\textbf{\@title}%
            """
            + email_footer
            + r"""
            }
            \fancyfoot[""" + even_page_num_pos + r"""E,""" + odd_page_num_pos + r"""O]{%
                \py@HeaderFamily\thepage%
            }
          }
          \fancypagestyle{plain}{%
            \fancyhf{}%
            \renewcommand{\headrulewidth}{0pt}
            \renewcommand{\footrulewidth}{1pt}
            \fancyhead[""" + even_page_num_pos + r"""E,""" + odd_page_num_pos + r"""O]{%
                \includegraphics[height=0.8cm]{""" + str(logo_path) + r"""}%
            }
            \fancyfoot[""" + even_page_num_pos.opposite()
            + r"""E,""" + odd_page_num_pos.opposite() + r"""O]{%
                \color{iBronze}Confidential Copy: Partners/End Users\\%
                \color{iBlack}\textbf{\@title}%
            """
            + email_footer
            + r"""
            }
            \fancyfoot[""" + even_page_num_pos + r"""E,""" + odd_page_num_pos + r"""O]{%
                \py@HeaderFamily\thepage%
            }
          }
        \makeatother
        \thispagestyle{empty}  % don't show foot on first page
        """,
        # define the title page
        "maketitle": r"""
        \makeatletter
        \begin{tikzpicture}[remember picture,overlay]
        %indurad logo links oben
        \node[] at ($(current page.north west)+(5.15cm,-3.4cm)$) {
            \includegraphics[width=5.1cm]{""" + str(logo_path) + r"""}
        };
        %balken unten, confidentiality field
        \fill [fill=iGold] ($(current page.south west)+(0,0.75cm)$) rectangle ($(current page.south east)+(0,1.5cm)$);
        \fill [rounded corners,fill=iBronze] ($(current page.south west)+(-.1,-.1)$) rectangle ($(current page.south west)+(4.5cm,2.5cm)$);
        \fill [fill=iBlack] ($(current page.south west)$) rectangle ($(current page.south east)+(0,0.75cm)$);
        \node [text=white] at ($(current page.south west)+(2.125cm,1.875cm)$){Confidential Copy};
        \node [text=white] at ($(current page.south west)+(2.125cm,1.25cm)$){Partners/End Users};
        \end{tikzpicture}

        \vskip 6cm

        {
        """  # noqa: E501
        + (r"""
            \begin{tikzpicture}
            \node[draw,rectangle, rounded corners, fill=iGold,iGold] at (1,1){\color{white}""" + kicker + r"""};
            \end{tikzpicture}
            \vskip 0.1em
        """ if kicker else "")
        + r"""
            {""" + iDocumentTitleFontSize + r"""\sffamily\bfseries \@title}
            \vskip 0.1em
        """
        + (r"""
            \begin{tikzpicture}
            \node[draw,rectangle, rounded corners, fill=iPortTurquoise,iPortTurquoise] at (1,1){\color{white}""" + subheading + r"""};
            \end{tikzpicture}
            \vskip 1em
        """ if subheading else "")  # noqa: E501
        + r"""
            \color{iGold}\normalsize

            \hspace{-2.5mm}
            \begin{tabularx}{\textwidth}{p{.08\textwidth}p{.52\textwidth}p{.08\textwidth}p{.32\textwidth}}
                author & \@author & version & """ + document_version + r""" \\
        """
        + (r"email & \href{mailto:""" + email + r"}{" + email + r"} &" if email else "")
        + r"""
            \end{tabularx}
        }
        \vskip 3em
        """
        + "".join(
            r"\includegraphics[height=9em]{" + str(solution_logo_path) + r"} \hskip 0.2em"
            for solution_logo_path in solution_logo_paths
        )
        + (r"""
        \clearpage
        \pagenumbering{gobble}
        \chapter*{Disclaimer}
        """ + disclaimer if insert_disclaimer else "")
        + r"""
        \color{black}
        \makeatother
        """  # noqa: E501
        ,
        "fontpkg": r"""
        \setmonofont{DejaVu Sans Mono}
        """,
        # Appendix
        "atendofbody": r"""
        """,
        # define chapter titles
        "fncychap": r"",
        "tableofcontents": r"""
        \clearpage
        \sphinxtableofcontents
        """,
        # Define where to start a new chapter
        "classoptions": ",twoside",
        "extraclassoptions": chapterstart,
        "sphinxsetup":
            # define colors
            f"TitleColor={Colors.iBlack.html}, "  # section
            f"InnerLinkColor={Colors.iPortTurquoise.html}, "  # links to sections
            f"OuterLinkColor={Colors.iPortTurquoise.html}, "  # links to websites
            f"VerbatimBorderColor={Colors.iBlack.html}, "  # border of code snippets
            # remove the ugly shadow of `contents`
            f"shadowsize=0pt, "
            # Table colors
            f"TableRowColorHeader={Colors.iGold.html}, "
            f"TableRowColorOdd={Colors.white.html}, "
            f"TableRowColorEven={Colors.black10.html}, "
            r"HeaderFamily=\sffamily\bfseries, "
    }
    # fmt: on
