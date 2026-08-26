%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Bezos Business Card
% LaTeX Class
% Version 1.0 (April 4, 2022)
%
% This class originates from:
% https://www.LaTeXTemplates.com
%
% Authors:
% Vel (vel@latextemplates.com)
% Candrika Pujnadati
%
% License:
% CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/)
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%----------------------------------------------------------------------------------------
%	CLASS CONFIGURATION
%----------------------------------------------------------------------------------------

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{CSBezosBusinessCard}[2022/04/04 Creodocs Bezos Business Card Class v1.0]

\DeclareOption*{\PassOptionsToClass{\CurrentOption}{extarticle}} % Pass through any extra options specified to the base class
\ProcessOptions\relax % Process class options

\LoadClass[8pt]{extarticle} % Load the base class with the default font size

%----------------------------------------------------------------------------------------
%	REQUIRED PACKAGES AND MISC CONFIGURATIONS
%----------------------------------------------------------------------------------------

\usepackage{array} % Required for manipulating table columns

\setlength{\parindent}{0pt} % No paragraph indentation

\pagestyle{empty} % Suppress headers and footers

\makeatletter
\let\@minipagerestore=\raggedright % Ensure all text in minipages is left aligned without hyphenation
\makeatother

%----------------------------------------------------------------------------------------
%	MARGINS
%----------------------------------------------------------------------------------------

\usepackage[
	top=0.25cm, % Top margin
	bottom=0.25cm, % Bottom margin
	left=0.5cm, % Left margin
	right=0.5cm, % Right margin
	%showframe % Uncomment to show frames around the margins for debugging purposes
]{geometry}

%----------------------------------------------------------------------------------------
%	FONTS
%----------------------------------------------------------------------------------------

\usepackage[T1]{fontenc} % Output font encoding for international characters
\usepackage[utf8]{inputenc} % Required for inputting international characters

\usepackage[
	default, % Use this as the default font
	oldstyle, % Use oldstyle figures, i.e. numbers that descend below the baseline
	light, % Use Light instead of Regular
	semibold, % Use SemiBold instead of Bold
]{raleway} % Use the Raleway font

\usepackage{microtype} % Improve typography
