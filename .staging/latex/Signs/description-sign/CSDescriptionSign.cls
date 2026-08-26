%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Description Sign
% LaTeX Class
% Version 1.1 (February 25, 2022)
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
\ProvidesClass{CSDescriptionSign}[2022/02/25 Creodocs Description Sign Class v1.1]

\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}} % Pass through any extra options specified to the base class
\ProcessOptions\relax % Process class options

\LoadClass{article} % Load the base class

%----------------------------------------------------------------------------------------
%	PACKAGES AND OTHER DOCUMENT CONFIGURATIONS
%----------------------------------------------------------------------------------------

\usepackage{etoolbox} % Required for conditional logic and easily changing commands

\pagestyle{empty} % Suppress headers and footers

\setlength{\parindent}{0pt} % Paragraph indentation
\setlength{\parskip}{20pt} % Space between paragraphs

\raggedright % Left align all text (suppress justification)

%----------------------------------------------------------------------------------------
%	MARGINS
%----------------------------------------------------------------------------------------

\usepackage{geometry} % Required for adjusting page dimensions and margins

\geometry{
	top=2.75cm, % Top margin
	bottom=2.25cm, % Bottom margin
	left=2.1cm, % Left margin
	right=2.1cm, % Right margin
	%showframe, % Uncomment to show how the type block is set on the page
}

%----------------------------------------------------------------------------------------
%	FONTS
%----------------------------------------------------------------------------------------

\usepackage[utf8]{inputenc} % Required for inputting international characters
\usepackage[T1]{fontenc} % Output font encoding for international characters

\usepackage[default]{lato} % Use the Lato font as the default
\DeclareRobustCommand\lseries{\fontseries{l}\selectfont} % Define a light font series

%---------------------------------------------------------------------------------
%	DOCUMENT CONTENT VARIABLES
%---------------------------------------------------------------------------------

\newcommand{\signtitle}[1]{\renewcommand{\signtitle}{#1}}
\newcommand{\signsubtitle}[1]{\renewcommand{\signsubtitle}{#1}}
\newcommand{\descriptiontext}[1]{\renewcommand{\descriptiontext}{#1}}
\newcommand{\additionaltext}[1]{\renewcommand{\additionaltext}{#1}}
