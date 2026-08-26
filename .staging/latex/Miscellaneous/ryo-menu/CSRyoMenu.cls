%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Ryo Menu
% LaTeX Class
% Version 1.0 (February 25, 2022)
%
% This class originates from:
% https://www.LaTeXTemplates.com
%
% Author:
% Vel (vel@latextemplates.com)
%
% License:
% CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/)
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%----------------------------------------------------------------------------------------
%	CLASS CONFIGURATION
%----------------------------------------------------------------------------------------

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{CSRyoMenu}[2022/02/25 Creodocs Ryo Menu Class v1.0]

\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}} % Pass through any extra options specified to the base class
\ProcessOptions\relax % Process class options

\LoadClass{article} % Load the base class

%----------------------------------------------------------------------------------------
%	PACKAGES AND OTHER DOCUMENT CONFIGURATIONS
%----------------------------------------------------------------------------------------

\usepackage{etoolbox} % Required for conditional logic and easily changing commands

\setlength{\parindent}{0pt} % Stop paragraph indentation

\usepackage{ulem} % For underlining
\renewcommand{\ULthickness}{3pt} % Thickness of the underline

\pagestyle{empty} % Suppress headers and footers

\raggedright % Suppress hyphenation across the whole document

%----------------------------------------------------------------------------------------
%	MARGINS
%----------------------------------------------------------------------------------------

\usepackage{geometry} % Required for adjusting page dimensions and margins

\geometry{
	top=3cm, % Top margin
	bottom=3cm, % Bottom margin
	left=4cm, % Left margin
	right=3.75cm, % Right margin
	%showframe, % Uncomment to show how the type block is set on the page
}

%----------------------------------------------------------------------------------------
%	FONTS
%----------------------------------------------------------------------------------------

\usepackage{fontspec} % Required for specifying custom fonts

\defaultfontfeatures{Ligatures=TeX} % To support LaTeX ligatures (`` and --)
\defaultfontfeatures{Path=Fonts/} % Specify the location of font files

% The serif font used by default or explicitly with \textrm{}/\rmfamily
\setmainfont{Lato}[
	UprightFont=*-Regular.ttf,
	BoldFont=*-Bold.ttf,
	ItalicFont=*-Italic.ttf,
	BoldItalicFont=*-BoldItalic.ttf
]

% Define a new font family for Lato Black
\newfontfamily\latoblack{Lato}[
	UprightFont=*-Black,
	ItalicFont=*-BlackItalic
]

%----------------------------------------------------------------------------------------
%	TABLES
%----------------------------------------------------------------------------------------

\usepackage{array} % Required for manipulating table columns

\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}} % Define a new right-aligned paragraph column type
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}} % Define a new left-aligned (no justification) paragraph column type
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}} % Define a new centered paragraph column type

%----------------------------------------------------------------------------------------
%	MENU ELEMENTS STYLING
%----------------------------------------------------------------------------------------

\renewcommand{\title}[1]{{\fontsize{42pt}{50pt}\selectfont\latoblack\textit{\uline{\MakeUppercase{#1}}}\par}} % Styling of the menu title

\newcommand{\menuitem}[3]{% Output a menu item as a table
	\begin{tabular}{@{} L{0.85\textwidth} @{} R{0.15\textwidth} @{}} % Table column widths and alignments
		\fontsize{\menuitemtitlefontsize}{\menuitemtitlefontsize}\selectfont\latoblack\MakeUppercase{#1} & \expandafter\ifstrempty\expandafter{#2}{}{\fontsize{\menuitempricefontsize}{\menuitempricefontsize}\selectfont\latoblack\currencysymbol #2}\\[2pt] % Menu item title and optional price
		\expandafter\ifstrempty\expandafter{#3}{}{\fontsize{\menuitemdescriptionfontsize}{1.16\menuitemdescriptionfontsize}\selectfont\itshape #3} % Optional menu item description
	\end{tabular}
	\vspace{10pt} % Vertical whitespace between menu items, KEEP THE LINE BELOW EMPTY so \menuitem commands can be used without newlines between them
	
}

\newcommand{\extrainfo}[1]{% Output extra menu information
	\vfill
	{\fontsize{\extrainfofontsize}{\extrainfofontsize}\selectfont\itshape#1}%
}

%---------------------------------------------------------------------------------
%	CURRENCY SYMBOLS
%---------------------------------------------------------------------------------

\newcommand{\currencysymbol}[1]{} % Default value of the currency symbol is empty unless otherwise changed

\newcommand{\determinecurrencysymbol}[1]{ % Uses the user-submitted currency cody to determine the symbol to use, does nothing if the code is not hard-coded below
	\ifboolexpr{ test {\expandafter\ifstrequal\expandafter{#1}{USD}} or test {\expandafter\ifstrequal\expandafter{#1}{AUD}} or test {\expandafter\ifstrequal\expandafter{#1}{CAD}} or test {\expandafter\ifstrequal\expandafter{#1}{FJD}} or test {\expandafter\ifstrequal\expandafter{#1}{HKD}} or test {\expandafter\ifstrequal\expandafter{#1}{JMD}} or test {\expandafter\ifstrequal\expandafter{#1}{NZD}} or test {\expandafter\ifstrequal\expandafter{#1}{SGD}} or test {\expandafter\ifstrequal\expandafter{#1}{TWD}} }{\renewcommand{\currencysymbol}{\$}}{} % The dollar sign for all the countries that use it (that are hardcoded here anyway)
	
	\expandafter\ifstrequal\expandafter{#1}{GBP}{\renewcommand{\currencysymbol}{\textsterling}}{} % GBP (English pounds)
	
	\ifboolexpr{ test {\expandafter\ifstrequal\expandafter{#1}{JPY}} or test {\expandafter\ifstrequal\expandafter{#1}{CNY}} }{\renewcommand{\currencysymbol}{\textyen}}{} % JPY or CNY (yen)
	
	\expandafter\ifstrequal\expandafter{#1}{EUR}{\renewcommand{\currencysymbol}{\texteuro}}{} % EUR (European euro)
	
	\expandafter\ifstrequal\expandafter{#1}{BRL}{\renewcommand{\currencysymbol}{R\$}}{} % BRL (Brazilian real)
	
	\expandafter\ifstrequal\expandafter{#1}{INR}{\renewcommand{\currencysymbol}{\rupee}}{} % INR (Indian rupee)
	
	\expandafter\ifstrequal\expandafter{#1}{RUB}{\renewcommand{\currencysymbol}{\RussianRuble}}{} % RUB (Russian ruble)
}

%------------------------------------------------

\usepackage{tfrupee} % Required for the rupee symbol

\usepackage{pgf}
\DeclareRobustCommand*{\RussianRuble}{% Define Russian ruble from https://tex.stackexchange.com/questions/260722/how-can-i-get-the-russian-ruble-sign Unfortunately the Lato font used by this template doesn't have the ruble glyph so we have to create it manually
	\begingroup
		\dimendef\H=0 %
		\settoheight\H{P}%
		\begin{pgfpicture}%
			\pgfsetlinewidth{.1\H}%
			\pgfsetrectcap
			\pgfsetmiterjoin
			\pgfmoveto{\pgfpoint{0pt}{.05\H}}%
			\pgflineto{\pgfpoint{0pt}{.95\H}}%
			\pgflineto{\pgfpoint{.35\H}{.95\H}}%
			\pgfpatharc{90}{-90}{.225\H}%
			\pgflineto{\pgfpoint{-.05\H}{.5\H}}%
			\pgfmoveto{\pgfpoint{-.05\H}{.34\H}}%
			\pgflineto{\pgfpoint{.38\H}{.34\H}}%
			\pgfusepath{stroke}%
			\pgfmoveto{\pgfpoint{-.175\H}{0pt}}%
			\pgfmoveto{\pgfpoint{.7\H}{0pt}}%
		\end{pgfpicture}%
	\endgroup
}
