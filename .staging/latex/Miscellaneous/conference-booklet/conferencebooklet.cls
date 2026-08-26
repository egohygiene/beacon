%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Conference Booklet
% Structural Definitions
% Version 1.0 (24/11/2019)
%
% This template originates from:
% http://www.LaTeXTemplates.com
%
% Original author:
% Maxime Lucas (ml.maximelucas@gmail.com) 
% Pau Clusella
% Modifications for LaTeX Templates by Vel (vel@LaTeXTemplates.com)
%
% License:
% GNU General Public License v3.0
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%----------------------------------------------------------------------------------------
%	CLASS CONFIGURATION
%----------------------------------------------------------------------------------------

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{conferencebooklet}[2019/12/22 LaTeX Templates Conference Booklet Class v1.0]

\DeclareOption*{\PassOptionsToClass{\CurrentOption}{scrbook}} % Pass through any options to the base class
\ProcessOptions\relax % Process given options

\LoadClass{scrbook} % Load the base class

%----------------------------------------------------------------------------------------
%	REQUIRED PACKAGES AND MISC CONFIGURATIONS
%----------------------------------------------------------------------------------------

\usepackage{graphicx} % Required for including images

\setcounter{secnumdepth}{-2} % Remove all section numbering

\usepackage{multicol} % Allows table cells to span multiple columns
\usepackage{longtable} % Allows the creation of tables that automatically wrap to the next page

\pagestyle{plain} % Use the plain page style for all headers and footers (only a page number)

\usepackage{scrhack} % Fixes compatibility issues between KOMA-Script and other packages

\usepackage{lastpage} % Required to determine the total number of pages

%----------------------------------------------------------------------------------------
%	MARGINS
%----------------------------------------------------------------------------------------

\usepackage[
	top=2.5cm, % Top margin
	bottom=2.5cm, % Bottom margin
	inner=1.5cm, % Inner margin
	outer=3cm, % Outer margin
	footskip=1.4cm, % Space from the bottom margin to the baseline of the footer
	headsep=0.8cm, % Space from the top margin to the baseline of the header
	headheight=0.5cm, % Height of the header
	%showframe % Uncomment to show the frames around the margins for debugging purposes
]{geometry}

%----------------------------------------------------------------------------------------
%	FONTS & TYPOGRAPHY
%----------------------------------------------------------------------------------------

\usepackage[utf8]{inputenc} % Required for inputting international characters
\usepackage[T1]{fontenc} % Output font encoding for international characters

\usepackage[sfdefault, lf]{carlito} % Use the Carlito family of sans-serif fonts with lining figures

\usepackage{microtype} % Improve typography

%----------------------------------------------------------------------------------------
%	COLOURS
%----------------------------------------------------------------------------------------

\usepackage[table]{xcolor} % Required for defining and using custom colours

\definecolor{myorange}{RGB}{255, 117, 40}
\definecolor{mygray}{RGB}{164, 168, 172}
\definecolor{mywhite}{RGB}{235, 238, 231}
\definecolor{myblue}{RGB}{52, 115, 116}

\newcommand{\primarycolor}{myblue}
\newcommand{\secondarycolor}{mywhite}

% Table colours
\newcommand{\tbg}{gray} % Event background
\newcommand{\tfg}{white} % Event foreground (text)
\newcommand{\tbc}{gray!25} % Break background

% Talk types colours
\newcommand{\IScolor}{myblue!65} % Invited speaker
\newcommand{\CTcolor}{white} % Contributed talk
\newcommand{\KLcolor}{myorange!45} % Keynote lecture
\newcommand{\ITcolor}{yellow!25} % Invited talk

%----------------------------------------------------------------------------------------
%	LINKS
%----------------------------------------------------------------------------------------

\usepackage{hyperref} % Required for links

\hypersetup{
	colorlinks=false,
	%urlcolor=\primarycolor, % Colour for \url and \href links
	%linkcolor=\primarycolor, % Colour for \nameref links
	hidelinks, % Hide the default boxes around links
}

%----------------------------------------------------------------------------------------
%	TABLE DEFINITIONS
%----------------------------------------------------------------------------------------

\usepackage{array} % Required for manipulating table columns

\newcommand{\tablebreak}[2]{\rowcolor{\tbc} #1 & \multicolumn{4}{c|}{\bfseries #2} \\ \hline } % Timetable conference break row
\newcommand{\eventtype}[2]{#1 & \multicolumn{4}{c|}{\cellcolor{\tbg}\color{\tfg}\bfseries #2} \\ \hline } % Timetable conference event row

\newcolumntype{L}[1]{>{\raggedright\let\newline\\\arraybackslash\hspace{0pt}}m{#1}} % Define a new left-aligned (no justification) column type
\newcolumntype{C}[1]{>{\centering\let\newline\\\arraybackslash\hspace{0pt}}m{#1}} % Define a new centred column type
\newcolumntype{R}[1]{>{\raggedleft\let\newline\\\arraybackslash\hspace{0pt}}m{#1}} % Define a new right-aligned column type

\newcommand{\IS}[4]{#1 & \cellcolor{\IScolor}IS & {\bfseries#2}\newline #3 & & #4 \\ \hline} % Invited speaker row
\newcommand{\CT}[4]{#1 & \cellcolor{\CTcolor}CT & {\bfseries#2}\newline #3 & & #4 \\ \hline} % Contributed talk row
\newcommand{\KL}[4]{#1 & \cellcolor{\KLcolor}KL & {\bfseries#2}\newline #3 & & #4 \\ \hline} % Keynote lecture row
\newcommand{\IT}[4]{#1 & \cellcolor{\ITcolor}IT & {\bfseries#2}\newline #3 & & #4 \\ \hline} % Invited talk row
\newcommand{\tutorial}[4]{#1 & & {\bfseries#2}\newline #3 & & #4 \\ \hline} % Tutorial row

%----------------------------------------------------------------------------------------
%	CHAPTER STYLING
%----------------------------------------------------------------------------------------

\newdimen\mybarpadding
\mybarpadding=1.5em\relax % Horizontal padding between the coloured bar and chapter name

\RedeclareSectionCommand[% Adjust the spacing around the \chapter command
	afterskip=4em plus 1pt minus 1pt,% Vertical whitespace under chapters
	beforeskip=-1pt, % Vertical whitespace before chapters
	level=0,% Chapters are the top level command
	toclevel=0,% Chapters are the top level command
]{chapter}

\setkomafont{chapter}{\normalfont\normalsize\bfseries\Huge} % Chapter font style

\RedeclareSectionCommand[% Adjust the spacing around the \section command
	afterskip=6pt,% Vertical whitespace under sections
	beforeskip=3pt, % Vertical whitespace before chapters
	level=1,% Sections are the second level command
	toclevel=1,% Sections are the second level command
]{section}

%------------------------------------------------

\renewcommand{\chapterlinesformat}[3]{%
	\ifthispageodd{% Odd pages have the coloured bar to the left of the chapter title
		\hfill% Coloured bar fills available width
		\raisebox{-0.2em}{\makebox[0pt][r]{\textcolor{\primarycolor}{\rule{\paperwidth}{1em}}}}% Coloured bar
		\hspace{\mybarpadding}% Padding between the chapter title and colour bar
		\mbox{#3}% Chapter title
	}{% Even pages have the coloured bar to the right of the chapter title
		\mbox{#3}% Chapter title
		\hspace{\mybarpadding}% Padding between the chapter title and colour bar
		\raisebox{-0.2em}{\makebox[0pt][l]{\textcolor{\primarycolor}{\rule{\paperwidth}{1em}}}}% Coloured bar
	}%
}

%----------------------------------------------------------------------------------------
%	ABSTRACT STYLING
%----------------------------------------------------------------------------------------

\newcommand{\abstract}[5]{
	\filbreak % Avoid page breaks within abstracts
	
	{\large \bfseries #1} % Title
	
	{\bfseries \itshape #2} \hfill {#3} % Author(s) and abstract type
	
	\textcolor{mygray}{#4} % Affiliation(s)
	
	#5 % Abstract text
}

%----------------------------------------------------------------------------------------
%	POSTER STYLING (SHORT)
%----------------------------------------------------------------------------------------

\newcommand{\poster}[3]{
	\filbreak % Avoid page breaks within abstracts
	
	{\large\bfseries #1}\\ % Title
	\hspace*{0.75cm} #2, \textit{#3} % Author and affiliation
	
}

%----------------------------------------------------------------------------------------
%	VERTICAL LINE IN PAGE MARGINS
%----------------------------------------------------------------------------------------

\usepackage[scale=1, angle=0, opacity=1]{background}
\backgroundsetup{contents={}}

\AddEverypageHook{%
	\ifthenelse{%
		\isodd{\thepage} \AND \thepage>1 \AND \NOT \thepage=\pageref{LastPage} % If odd page but not the first or last page
	}{%
		\backgroundsetup{
			color=\secondarycolor, % Bar colour
			position=current page.south east, % Position of the bar on the page
			nodeanchor=south east, % Anchor location inside the bar
			contents={\rule{10pt}{0.66\paperheight}} % Bar width and height
			}
	}{}
	%
	\ifthenelse{% 
		\NOT \isodd{\thepage} \AND \NOT \thepage=\pageref{LastPage} % If even page but not the last page
	}{%
		\backgroundsetup{
			color=\secondarycolor, % Bar colour
			position=current page.south west, % Position of the bar on the page
			nodeanchor=south west, % Anchor location inside the bar
			contents={\rule{10pt}{0.66\paperheight}} % Bar width and height
			}
	}{}
	%
	\BgMaterial % Output the background set up above
}

%----------------------------------------------------------------------------------------
%	TALK TYPE CIRCLE DEFINITIONS
%----------------------------------------------------------------------------------------

\newcommand{\circlegeneric}[2]{\tikz[baseline={([yshift=-.8ex]current bounding box.center)}]  \node[circle, inner sep=3pt, minimum size=0.5em, color=black, fill=#1]{\small \bfseries #2};} % Generic definition of a circle with a custom colour and 2 letters in it

\newcommand{\KLtag}{\circlegeneric{\KLcolor}{KL}} % Keynote lecture circle
\newcommand{\IStag}{\circlegeneric{\IScolor}{IS}} % Invited speaker circle
\newcommand{\CTtag}{\circlegeneric{\CTcolor}{CT}} % Contributed talk circle
\newcommand{\ITtag}{\circlegeneric{\ITcolor}{IT}} % Invited talk circle

%----------------------------------------------------------------------------------------
%	PACKAGES THAT CLASH AND MUST BE LOADED LAST
%----------------------------------------------------------------------------------------

\usepackage{pdfpages} % Required for including a full-page image for the cover
