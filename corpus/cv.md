# Antoine Hocquet – CV & Portfolio

> Source data for the itw-me RAG corpus, transformed 1:1 from `portfolio_antoine.yaml`.
> LaTeX macros and escape sequences have been converted to plain Markdown / Unicode
> so the content reads cleanly for both humans and the retrieval and answer pipeline.
> Citation keys such as `[hocquet2019finite]` refer to entries in the Publications
> section below (or, where the key does not match a title there, to an external
> reference not otherwise listed in this corpus).

## Education

### 2024 – Applied Data Science Program (Professional Certificate)
**Institution:** MIT Professional Education

Completed an intensive 12 weeks mentor-led program focused on real-world AI applications.
Gained experience in data analysis, supervised and unsupervised learning, time series,
network analysis, deep learning, and recommender systems.

**Stack:** Data wrangling, feature engineering, decision trees, time series forecasting, neural networks,
recommender systems, network analysis, model evaluation.
Python's foundational libraries (`Pandas`, `scikit-learn`, etc.); also: `statsmodels`, `NetworkX`, `TensorFlow`, `Keras`, `Surprise`.

### 2012–2016 – Ph.D. in Applied Mathematics, Highest Distinction
**Institution:** École Polytechnique, France

Doctoral thesis on the stochastic Landau–Lifshitz–Gilbert equation under Gaussian noise, combining probability theory, partial differential equations, and numerical analysis.
Successfully defended with highest honors (*félicitations du jury*), resulting in three peer-reviewed publications with significant impact.
Developed expertise in high-performance scientific computing using MATLAB, Python, and FreeFem++.
Completed a structured pedagogical training component through 64 hours/year of teaching duties (graduate tutorials in numerical analysis and supervision of Bachelor-level projects), fulfilling the *agrégation* teaching practicum and formal qualification for permanent secondary or higher education positions in France.

### 2011–2012 – Master's degree in Mathematics, Highest Honors
**Institution:** École Normale Supérieure (ENS Cachan, Bretagne campus), France

Admitted through a highly competitive national examination in Spring 2011 to one of France's top graduate schools.

### 2011 – Higher Education Teaching Certification ("Agrégation")
**Institution:** Université d'Orsay

French national advanced teaching qualification in mathematics.

### 2008–2010 – Bachelor of Science, Health & Technology
**Institution:** Orsay University, France

### 2005–2007 – Classe préparatoire aux grandes écoles
**Institution:** MPSI Lycée Sainte-Marie d'Antony, MP Lycée Lakanal, Sceaux

## Experience

### 2022–2024 – Postdoc
**Institution:** Technische Universität Berlin

Project entitled "Rough Stochastic Analysis" – Supervision: Peter Friz.
Teaching: graduate course "Rough Stochastic McKean–Vlasov Equations", TUB.
Seminar: Stochastic Analysis, Rough paths and applications in Data Science.
Grant prospect.

### 2019–2022 – Postdoc
**Institution:** Technische Universität Berlin

Project entitled "Control of Stochastic mean-field equations with applications to brain networks" – Supervision: Wilhelm Stannat.
Teaching: graduate course "Numerics for Stochastic Partial Differential Equations", Berlin Mathematical school.
Seminar: Stochastic PDEs and applications, TUB.
Workshop organization (Scholarship), Bonn University.

### 2016–2019 – Postdoc
**Institution:** Technische Universität Berlin

Project funded by the German Research Foundation, entitled "Rough Paths, Stochastic Partial Differential Equations and Related Topics".
Supervision: Peter K. Friz, Martina Hofmanová, Wilhelm Stannat.
Teaching: master theses supervision.

### 2012–2016 – PhD Candidate & Teaching Assistant
**Institution:** École Polytechnique, Centre de Mathématiques Appliquées, Palaiseau, France

Conducted original research on the stochastic Landau–Lifshitz–Gilbert equation under Gaussian noise, integrating probability theory, partial differential equations, and numerical analysis.
Designed and implemented high-performance simulations in MATLAB, Python, and FreeFem++.
Published three peer-reviewed articles and presented findings at international conferences.
Delivered 64 hours/year of teaching: exercise sessions, graduate-level numerical analysis tutorials, and supervision of Bachelor and Master theses.

## Publications

### The Landau-Lifshitz-Gilbert equation driven by Gaussian noise (PhD thesis, 2015)
**Citation:** A. Hocquet. "The Landau-Lifshitz-Gilbert equation driven by Gaussian noise." PhD thesis, École Polytechnique, 2015.
**URL:** https://hal.science/tel-01265433/

This thesis is devoted to the influence of a noise term in the stochastic Landau-Lifshitz-Gilbert Equation (SLLG). It is
a nonlinear stochastic partial differential equation with a non-convex constraint on the modulus of the solutions.
First, we study in chapter 1 the question of local solvability. Using classical properties of stochastic integration
with Banach space-valued processes, we propose a mild formulation, and give the existence and uniqueness of a local
solution in any dimension, for a Gaussian noise, regular in space. Secondly, we focus on the specific study of SLLG
in a two-dimensional space domain. Chapter 2 deals with the existence of a strong solution, in the probabilistic sense.
Using the energy formula, we give a method to obtain uniquely a global solution in time. Chapter 3 gives uniqueness of
weak solutions, provided that the energy satisfies a super-martingale property. This is the stochastic counterpart of
a known deterministic result giving the uniqueness of weak solutions, knowing that the energy decreases. Chapter 4
gives the existence, in the so-called "overdamped case", of solutions that blow-up in finite time. We prove that,
unlike the deterministic case, a singularity may appear with positive probability, regardless of the initial data chosen.
Then we return to the case of general dimension of space, providing in chapter 5 a new time semi-discrete scheme for SLLG.
This chapter is based on an article in collaboration with F. Alouges and A. De Bouard. We show the convergence in law
of a projection-type scheme for SLLG, which has the advantage of respecting exactly the local constraint on the magnitude.
This scheme treats the case of a rather general noise term regularized in space but infinite-dimensional.
In Chapter 6, we show how to implement it with a finite element dicretization in space, and we give a practical method
for approaching a regular noise in this framework. We also evidence numerical blow-up of the solutions, despite the presence
of a gyromagnetic term, and of a more general noise than that of Chapter 4.

### A semi-discrete scheme for the Stochastic Landau-Lifshitz equation (2014)
**Citation:** F. Alouges, A. De Bouard, A. Hocquet. "A semi-discrete scheme for the Stochastic Landau-Lifshitz equation." *Stochastic Partial Differential Equations: Analysis and Computations*, 2(3):281–315, 2014.
**URL:** https://link.springer.com/article/10.1007/s40072-014-0033-7

A new convergent time semi-discrete scheme for the stochastic Landau–Lifshitz–Gilbert equation is investigated. The scheme is only
linearly implicit and does not require the resolution of a nonlinear problem at each time step. Using a martingale approach,
we prove the convergence in law of the scheme up to a subsequence.

### Struwe-like solutions of the stochastic harmonic map flow (2018)
**Citation:** A. Hocquet. "Struwe-like solutions of the stochastic harmonic map flow." *Journal of Evolution Equations*, 18(3):1189–1228, 2018.
**URL:** https://link.springer.com/article/10.1007/s00028-018-0437-3

New results on the well-posedness of the two-dimensional Stochastic Harmonic Map flow are obtained. The study of this evolution equation (SPDE) is motivated by the
Landau–Lifshitz–Gilbert model for thermal fluctuations in micromagnetics. We first construct strong solutions that are locally
as regular as permitted by the data. It that sense, these maps are a counterpart of the so-called "Struwe solutions" of the
deterministic model. We then provide a natural criterion of uniqueness that extends A. Freire's Theorem to the stochastic case.
Both results are obtained under the condition that the noise term has a trace-class covariance in space.

### An energy method for rough partial differential equations (2018)
**Citation:** A. Hocquet, M. Hofmanová. "An energy method for rough partial differential equations." *Journal of Differential Equations*, 265(4):1407–1466, 2018.
**URL:** https://www.sciencedirect.com/science/article/pii/S002203961830189X

A well-posedness and stability result for a class of nondegenerate linear parabolic equations driven by geometric
rough paths is presented. More precisely, we introduce a notion of weak solution that satisfies an intrinsic formulation of the equation
in a suitable Sobolev space of negative order. Weak solutions are then shown to satisfy the corresponding energy estimates
which are deduced directly from the equation. Existence is obtained by showing compactness of a suitable sequence of approximate
solutions whereas uniqueness relies on a doubling of variables argument and a careful analysis of the passage to the diagonal.
Our result is optimal in the sense that the assumptions on the deterministic part of the equation as well as the initial condition
are the same as in the classical PDEs theory.

### Finite-time singularity of the stochastic harmonic map flow (2019)
**Citation:** A. Hocquet. "Finite-time singularity of the stochastic harmonic map flow." *Annales de l'Institut Henri Poincaré, Probabilités et Statistiques*, 55(2):1011–1041. Institut Henri Poincaré, 2019.
**URL:** https://projecteuclid.org/euclid.aihp/1557820840

The influence of an infinite dimensional Gaussian noise on the bubbling phenomenon for the stochastic harmonic map flow
from the two-dimensional unit disc onto the sphere is investigated. The diffusion term is assumed to have range one pointwisely in the tangent space,
so that the noise preserves the 1-corotational symmetry of solutions. Under the assumption that its space-correlation is of trace class
(in some appropriate Hilbert space), it is proved that the noise generates blow-up with positive probability. This scenario happens
no matter how the initial data is chosen, provided it fulfills the latter symmetry assumption.

### Generalized Burgers equation with rough transport noise (2020)
**Citation:** A. Hocquet, T. Nilssen, W. Stannat. "Generalized Burgers equation with rough transport noise." *Stochastic Processes and their Applications*, 130(4):2159–2184, 2020.
**URL:** https://www.sciencedirect.com/science/article/abs/pii/S030441491830721X

A new technique for studying well posedness and energy estimates for evolution equations with a rough transport term is introduced.
The technique is based on finding suitable space–time weight functions for the equations at hand. As an example, the well posedness
of the generalized viscous Burgers equation perturbed by a rough path transport noise is studied.

### An Itô formula for rough partial differential equations and some applications (2020)
**Citation:** A. Hocquet, T. Nilssen. "An Itô formula for rough partial differential equations and some applications." *Potential Analysis*, 53(1):1–56, 2020.
**URL:** https://doi.org/10.1007/s11118-020-09830-y

Existence, uniqueness and regularity for solutions of rough parabolic equations with a rough transport term is established.
To do so, we introduce a concept of "differential rough driver", which comes with a counterpart of the usual controlled paths spaces
in rough paths theory, built on Sobolev spaces. We also define a natural notion of geometricity in this context, and show how it relates
to a product formula for controlled paths. In the case of pure transport noise, we use this framework to prove an Itô Formula (in the sense
of a chain rule) for Nemytskii operators. Our method is based on energy estimates, and a generalization of the Moser Iteration argument to
prove boundedness of a dense class of solutions of parabolic problems as above. In particular, we avoid the use of flow transformations
and work directly at the level of the original equation. As an application of these results, we prove existence and uniqueness of a suitable
class of Lp-solutions of parabolic equations with multiplicative noise. Another related development is the homogeneous Dirichlet boundary
problem on a smooth domain, for which a weak maximum principle is shown under appropriate assumptions on the coefficients.

### Quasilinear rough partial differential equations with transport noise (2021)
**Citation:** A. Hocquet. "Quasilinear rough partial differential equations with transport noise." *Journal of Differential Equations*, 276:43–95, 2021.
**URL:** https://www.sciencedirect.com/science/article/abs/pii/S0022039620306562

The Cauchy problem for a quasilinear equation with transport rough input is studied. Using energy estimates, we provide sufficient
conditions that guarantee existence in any dimension, and uniqueness in the case when the underlying rough path is divergence-free.
We then focus on the one-dimensional scenario, with slightly more regular coefficients. Improving the a priori estimates of the first results,
we prove existence of a class of solutions whose spatial derivatives satisfy a Ladyzhenskaya–Prodi–Serrin type condition. Uniqueness is shown
in the same class, by obtaining an estimate on the difference of two solutions. The latter is obtained by establishing a link with a certain
backward dual equation combined with a (rough) iteration lemma à la Moser.

### Existence, uniqueness and regularity for the stochastic Ericksen-Leslie equation on surfaces (2021)
**Citation:** A. De Bouard, A. Hocquet, A. Prohl. "Existence, uniqueness and regularity for the stochastic Ericksen-Leslie equation on surfaces." *Nonlinearity*, 34(6):4057–4088, 2021.
**URL:** https://iopscience.iop.org/article/10.1088/1361-6544/ac022e/meta

Existence and uniqueness for the liquid crystal flow driven by colored noise on the two-dimensional torus is established.
After giving a natural uniqueness criterion, we prove local solvability in Lebesgue spaces for any level of integrability larger than two.
Thanks to a bootstrap principle together with a Gyöngy–Krylov-type compactness argument, this will ultimately lead us to prove the existence
of a particular class of global solutions which are partially regular, strong in the probabilistic sense, and taking values in the critical energy space.

### Non-autonomous evolution equations and the multiplicative sewing lemma (2021)
**Citation:** A. Gerasimovics, A. Hocquet, T. Nilssen. "Non-autonomous evolution equations and the multiplicative sewing lemma." *Journal of Functional Analysis*, 281(10):109200, 2021.
**URL:** https://doi.org/10.1016/j.jfa.2021.109200

Existence, uniqueness and regularity for local solutions of generic rough parabolic equations with subcritical noise are established,
on scales of Banach spaces. Besides dealing with non-autonomous evolution equations, our results also allow for unbounded operations
in the noise term (up to some critical loss of regularity depending on that of the rough path $X$). As a technical tool, we introduce
a version of the multiplicative sewing lemma, which allows to construct the so-called product integrals in infinite dimensions.
We later use it to construct a semigroup analogue for the non-autonomous linear PDEs as well as show how to deduce the semigroup version
of the usual sewing lemma.

### Optimal control of mean field equations with monotone coefficients and applications in neuroscience (2021)
**Citation:** A. Hocquet, A. Vogler. "Optimal control of mean field equations with monotone coefficients and applications in neuroscience." *Applied Mathematics and Optimization*, 84(2):1925–1968, 2021.
**URL:** https://link.springer.com/article/10.1007/s00245-021-09816-1

The optimal control problem associated with certain quadratic cost functionals depending on the solution of a generic stochastic mean-field type evolution equation is studied.
This is done under assumptions that enclose a system of FitzHugh–Nagumo neuron networks, and where for practical purposes the control is deterministic. To do so, we assume that we are given a drift coefficient that satisfies a one-sided Lipschitz condition, and that the dynamics satisfies an almost sure boundedness property. The mathematical treatment we propose follows the lines of the recent monograph of Carmona and Delarue for similar control problems with Lipschitz coefficients. After addressing the existence of minimizers via a martingale approach, we show a maximum principle, and numerically investigate a gradient algorithm for the approximation of the optimal control.

### A pathwise stochastic Landau-Lifshitz-Gilbert equation with application to large deviations (2023)
**Citation:** E. Gussetti, A. Hocquet. "A pathwise stochastic Landau-Lifshitz-Gilbert equation with application to large deviations." *Journal of Functional Analysis*, 285(9):110094, 2023.
**URL:** https://www.sciencedirect.com/science/article/abs/pii/S0022123623002513

Using a rough path approach, existence, uniqueness and regularity for the stochastic Landau-Lifshitz-Gilbert equation with Stratonovich noise on the one-dimensional torus is established.
As a main result we show the continuity of the so-called Itô-Lyons map in the natural energy spaces at any level of regularity. The proof proceeds in two steps.
First, based on an energy estimate space together with a compactness argument we prove existence of a unique solution, implying the continuous dependence in a weaker norm.
This is then strengthened in the second step where the continuity in the optimal norm is established through an application of the rough Gronwall lemma.
Our approach is direct and does not rely on any transformation formula, which permits to treat multidimensional noise. As an easy consequence we then deduce a Wong-Zakai type result,
a large deviation principle, as well as a support theorem.

### Rough stochastic differential equations (to appear, CPAM)
**Citation:** P.K. Friz, A. Hocquet, K. Lê. "Rough stochastic differential equations." To appear in *CPAM*.
**URL:** https://arxiv.org/abs/2106.10340

A simultaneous generalization of Itô's theory of stochastic and Lyons' theory of rough differential equations is established. The interest in such a unification comes from a variety of applications, including pathwise stochastic filtering, control and the conditional analysis of stochastic systems with common noise.

### An application of the multiplicative Sewing Lemma to the high order weak approximation of stochastic differential equations (2023)
**Citation:** A. Hocquet, A. Vogler. "An application of the multiplicative Sewing Lemma to the high order weak approximation of stochastic differential equations." *Stochastic Processes and their Applications*, 165:183–217, 2023.
**URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304414923001692

A variant of the multiplicative Sewing Lemma in [Gerasimovičs, Hocquet, Nilssen; J. Funct. Anal. 281 (2021)] is introduced.
It yields arbitrary high order weak approximations to stochastic differential equations, extending the cubature approximation
on Wiener space introduced by Lyons and Victoir. Our analysis allows to derive stability estimates and explicit weak convergence rates.
As a particular example, a cubature approximation for stochastic differential equations driven by continuous Gaussian martingales is given.

### Quasilinear rough evolution equations (2023)
**Citation:** A. Hocquet, A. Neamțu. "Quasilinear rough evolution equations." *The Annals of Applied Probability*, 34(5):4268–4309, 2023.
**URL:** https://projecteuclid.org/journals/annals-of-applied-probability/volume-34/issue-5/Quasilinear-rough-evolution-equations/10.1214/24-AAP2065.short

The abstract Cauchy problem for quasilinear parabolic equations in Banach spaces driven by a two-step rough path is investigated.
We explore the mild formulation that combines functional analysis techniques and controlled rough paths theory which entail the local well-posedness of such equations.
We apply our results to the stochastic Landau–Lifshitz–Gilbert and Shigesada–Kawasaki–Teramoto equations.

### Unbounded rough drivers, rough PDEs and applications (arXiv preprint, 2025)
**Citation:** A. Hocquet, M. Hofmanová, T. Nilssen. "Unbounded rough drivers, rough PDEs and applications." arXiv preprint arXiv:2501.01186.
**URL:** https://arxiv.org/abs/2501.01186

A summary of recent contributions in the field of rough partial differential equations is given.
For that purpose we rely on the formalism of "unbounded rough driver". We present applications to concrete models including Landau-Lifshitz-Gilbert, Navier-Stokes and Euler equations.

### McKean-Vlasov equations with rough common noise (arXiv preprint, 2025)
**Citation:** A. Hocquet, P.K. Friz, K. Lê. "McKean-Vlasov equations with rough common noise." arXiv preprint arXiv:2507.13149.
**URL:** https://arxiv.org/abs/2507.13149

Well-posedness for McKean–Vlasov equations with rough common noise and progressively measurable coefficients is shown.
Our results are valid under natural regularity assumptions on the coefficients, in agreement with the respective requirements
of Ito and rough path theory. To achieve these goals, we work in the framework of rough stochastic differential
equations recently developed by the authors of this article.

## Teaching

### 2012–2016 – EV2 courses and exercise sessions
**Institution:** École Polytechnique

Bachelor-level courses for foreign students, newcomers to the École Polytechnique from a wide variety of nationalities (various european countries, Brasil, China, Chile, Russia etc.).
The aim of these lectures is to ease transition from foreign educational system (High School or undergraduates). Another goal is to provide students with the equivalent level of a preparatory class outing ("CPGE").
The areas I taught include:
- Introduction to Probability (elementary measure theory, Bernoulli laws, law of large numbers etc.)
- Real and Complex analysis (sequences, series, analytic functions, multidimensional differential calculus, etc.)
- Linear ordinary differential equations.

The EV2 teaching is accompanied with pure exercise sessions, in which the students are asked to look at problems and go to the blackboard, one after another. In addition to learning mathematical rigor (proper mathematical proofs, logic and set theory),
an important goal of these sessions is to facilitate the learning of French, through interaction with the teacher and other students.

### 2012–2016 – Supervision of computer science sessions for 1st and 2nd years
**Institution:** École Polytechnique

Students are introduced to concrete examples of finite element discretizations (in connection with the course on Partial Differential Equations and Scientific Computing).
Then, students are invited to implement these models using scientific software (Scilab or Freefem++).
The objective is to familiarize students with the use of scientific software, and to make them aware of the importance of numerical analysis in the context of scientific computing.

### 2012–2016 – Tutoring sessions for 2nd years
**Institution:** École Polytechnique

Exercises related to the lecture notes of numerical analysis of G. Allaire and F. Alouges.
The course given at École Polytechnique introduces the concept of variational formulation for a given partial differential equation,
as well as the definition of Schwartz distributions and Sobolev spaces.

### 2014–2015 – Supervision of projects for 2nd and 3rd years
**Institution:** École Polytechnique

The objective is to make students responsible for a numerical analysis project of their choice, oriented towards engineering and meeting a concrete objective (e.g. using excess heat produced by computers to heat a building, constructing an optimal road network, etc.).
The students are invited to discuss with the supervisor the relevance of their mathematical model and the approximations used.
The project is then evaluated by the supervisor and professors in the lab.

### 2015–2016 – In-depth knowledge projects for undergraduate students
**Institution:** École Polytechnique

Supervision of groups of 5 foreign students are told to investigate a topic of their choice,
suggested by the supervisor (e.g. 'Quaternions and the Banach-Tarski paradox', or 'the mathematics of quantum mechanics').
The supervisor meets the group weekly, until the end of the trimester where they have to provide a manuscript.
They are also asked to defend their work in front of the other classmates.

### 2021–2022 – M2 course: Numerical Analysis for Stochastic PDEs
**Institution:** Berlin Mathematical School

The objective is to familiarize students with relatively recent results on strong and weak error analysis
of numerical schemes for stochastic partial differential equations. An overview of approximation theory for ordinary
stochastic differential equations is also given as an introduction.

### 2023–2024 – M2 course: Rough Stochastic McKean–Vlasov Equations
**Institution:** Technische Universitaet Berlin

The objective is to familiarize students with the theory of McKean–Vlasov equations with rough common noise.
The course covers the recent results on well-posedness, regularity and applications to control theory.
The course is based on recent contributions by P.K. Friz, A. Hocquet and K. Lê.

## Numerical Projects

### RecSysEcho
A modular recommender system built from the Million Song Dataset. Implements content-based and collaborative filtering
(KNN, SVD/SVD++), with year and genre features. Structured using MLOps best practices: testing, CI/CD, command-line scripts, and `Makefile`.

**Stack:** Python, pandas, scikit-learn, pytest, Makefile.
**Repository:** https://github.com/AntoineHocquet/RecSysEcho

### FHN Optimal Control (Rust)
Reimplementation in Rust of a neuroscience control problem using stochastic FitzHugh–Nagumo networks. Features gradient descent optimization via adjoint equations.
Emphasizes performance and reproducibility in a 100% Rust-native pipeline.

**Stack:** Rust (CLI, Plotters, Cargo), Euler–Maruyama scheme.
**Repository:** https://github.com/AntoineHocquet/fhn

### Boxing AI
A reinforcement learning and adversarial training environment where two agents learn to fight in a 2D ring.
Uses PyTorch for neural control, adversarial updates, and animated visualizations. MLOps tooling included (unit tests, CLI, `Makefile`).

**Stack:** Python, PyTorch, matplotlib, pytest.
**Repository:** https://github.com/AntoineHocquet/boxing

### Automated CV/Letter Generator
LLM-powered app to generate LaTeX cover letters from job ads. Includes Streamlit UI, Docker-based LaTeX compilation, and Mistral API integration.
Designed with privacy-first and automation-ready mindset.

**Stack:** Python, Streamlit, LangChain, LaTeX, Docker, Mistral API.
**Repository:** https://github.com/AntoineHocquet/automated-cv

### RAG-Formulate
A document reformulation tool using retrieval-augmented generation (RAG). Embedding-based fragment selection (FAISS) + LLM rewriting
with strict constraints. Modular pipeline with full testing suite.

**Stack:** Python, FAISS, Mistral API, pytest.
**Repository:** https://github.com/AntoineHocquet/rag-formulate

### SpaceY (Rocket Landing Prediction)
End-to-end ML project predicting SpaceX Falcon 9 landings. Includes data scraping, SQL EDA, geospatial plots, multiple ML models, and interactive Dash dashboard. Follows reproducible MLOps design.

**Stack:** Python, pandas, scikit-learn, SQL, Dash, folium, Makefile, argparse.
**Repository:** https://github.com/AntoineHocquet/spaceY

### LLG Simulation App
Scientific computing pipeline for solving the Landau–Lifshitz–Gilbert (LLG) equation on a 2D disk using finite elements. Leverages FreeFEM++,
Docker, and Python CLI for full reproducibility. Features 3D static/animated visualizations and parameter overrides via command line.

**Stack:** FreeFEM++, Python (matplotlib, pandas), Docker, CLI, JSON config.
**Repository:** https://github.com/AntoineHocquet/llg

### LLG 1D Simulation Pipeline
Hybrid C++/Python pipeline for simulating a 1D nonlinear PDE representing magnetization dynamics. Uses finite differences in C++ for
performance, Python for orchestration, visualization, and CI automation. Includes Docker support and GitHub Actions testing.

**Stack:** C++, Python (matplotlib, pandas), Makefile, GitHub Actions CI.
**Repository:** https://github.com/AntoineHocquet/1dllg

### GeoNavRL
Reinforcement learning environment for simulating last-mile delivery navigation. Inspired by real-world challenges in logistics
and urban mapping, this project explores how agents can learn to make optimal routing decisions in uncertain, noisy,
and geospatially constrained environments.

**Stack:** Python, PyTorch, stable-baselines3, geopandas, shapely, folium, matplotlib, osmnx, gymnasium, pytest, Docker, Makefile.
**Repository:** https://github.com/AntoineHocquet/GeoNavRL

### dida-roof-seg
A deep learning model for semantic segmentation of roofs in satellite images, trained on the DIDA dataset.
Implements a U-Net architecture with data augmentation, early stopping, and model checkpointing.

**Stack:** Python, PyTorch, matplotlib, Makefile.
**Repository:** https://github.com/AntoineHocquet/dida-roof-seg

### fraud-DL
A tiny, simple and modular-ish baseline for fraud detection on the Kaggle ULB Credit Card Fraud dataset.
Focus: clarity > features. Imbalanced learning done the simple way. While it avoids the use of PyTorch,
it provides a quick DL-ish flavor using `sklearn.neural_network.MLPClassifier`.

**Stack:** Python, pandas, scikit-learn, matplotlib.
**Repository:** https://github.com/AntoineHocquet/fraud-DL

## Research

### Micromagnetism, Landau-Lifshitz-Gilbert equation and related topics (2012–2016)

The stochastic Landau-Lifshitz-Gilbert equation was introduced in [landau1935theory] to model the evolution
of the magnetization of a given ferromagnetic domain $\mathscr{O} \subset \mathbb{R}^n$ for $1 \le n \le 3$.
It takes the form of the SPDE

$$
du_t = \left(\beta u_t \times H_{\mathrm{eff}}(u_t) - \alpha u_t \times (u_t \times H_{\mathrm{eff}}(u_t))\right) dt + \epsilon u_t \times dW_t, \quad |u_t(\omega,x)|_{\mathbb{R}^3} \equiv 1 \tag{SLLG}
$$

on $(0,T] \times \mathscr{O}$, where the effective field $H_{\mathrm{eff}}(u) = -\nabla E(u)$, $E$ being the total energy of the system
(the unknown $u_t(x,\omega)$ takes values in the unit sphere).
Understanding the effect of the noise term $dW$ (modelizing thermal fluctuations) is an important mathematical question, for instance to study long term stability properties of magnetized materials (such as information storage devices, see e.g. [kohn2005magnetic]).

Formally, the case when $E = \frac{1}{2}\int |\nabla u|^2 dx$ and $\alpha = 1 \gg |\beta|$ reduces to the *stochastic harmonic map flow*

$$
du_t = \left(\Delta u_t + u_t |\nabla u_t|^2\right) dt + \epsilon u_t \times dW_t, \quad |u_t(\omega,x)|_{\mathbb{R}^3} \equiv 1 \tag{SHMF}
$$

which was originally studied by Eells and Sampson in [eells1964harmonic] when $\epsilon = 0$ to construct harmonic maps between two manifolds.
It is related to a number of physical models displaying spherical constraints (including Ericksen-Leslie system for liquid crystals [de2021existence] or Funaki's motion of a random string [bruned2022geometric]).

An important open problem for Eq. (SLLG)–(SHMF) when $d \ge 2$ is to understand the blow-up behaviour of solutions in presence of noise, as was partly addressed in my contributions [alouges2014semi; hocquet2015landau; hocquet2018struwe; hocquet2019finite; de2021existence].

A few years ago, Pierre Raphaël and his co-authors showed that the deterministic harmonic map flow explosion is stable under small perturbations of the initial data [raphael2013stable], in an equivariance-preserving direction, which is also the type of symmetry I considered in [hocquet2019finite] when I showed the existence of singular solutions for a (well-chosen) degenerate noise term.
This contrasts with [merle2013blow] where it is shown existence, but instability, of initial data leading to the explosion for the deterministic version of Eq. (SLLG). It appears that the instability is due to the necessary extra degree of freedom of the solutions, compared to Eq. (SHMF) for which a reduction to a scalar problem via the equivariant ansatz is possible.

This leads to the conjecture that a fully non-degenerate noise term should prevent the explosion phenomenon to occur, which is a problem I would like to address in the future.

### Rough partial differential equations (2016–2019)

Introduced by Lyons in [lyons1998differential; lyons2002system], rough paths allow to describe solutions of ordinary differential equations controlled by an arbitrary irregular signal.
Rough *partial* differential equations are special cases of singular PDEs, where the irregularity occurs in a particular direction (usually the "time" variable).
Despite this specificity, they are relevant in a number of physical models where the irregularity appears as a stochastic process indexed by a time variable (the most common example is Brownian motion).

Fixing the sample parameter $\omega \in \Omega$, one may describe the models Eq. (SLLG)–(SHMF) as particular instances of the generic RPDE[^rpde]

$$
\begin{cases}
du_t - (A_t(u_t)u_t + N_t(u_t))\,dt = \displaystyle\sum_{i=0}^{d} F_i(u_t)\, d\mathbf{X}^i_t, \quad \text{on } [0,T] \times \mathbb{R}^n, \\
u_0 \in L^p(\mathbb{R}^n).
\end{cases} \tag{ansatz-RPDE}
$$

An important aim of my previous research was to develop a general methodology to obtain *a priori estimates* for partial differential
equations of this type, as partly carried out in [hocquet2018energy; hocquet2020ito; hocquet2020generalized; hocquet2021quasilinear].
A different – though related – purpose is to find rough counterparts of functional analytic techniques which fail in the setting of Itô's
stochastic calculus, due to regularity or measurability issues. This direction was partly explored in the recent contributions
[gerasimovics2021non; hocquet2022weak; hocquet2022quasilinear], where a generalization of the Sewing Lemma in operator algebras was introduced.

[^rpde]: Here $A_\cdot$ is a family of (possibly non-linear) operators, $\mathbf{X}^i, i = 0,\dots,d \in \mathbb{N} \cup \{\infty\}$ is a rough path with values in some functional space (for the spatial variable $x \in \mathbb{R}^n$), while $F$ and $N$ are non-linearities.

### Mean field control in neuroscience (2019–2022)

FitzHugh proposed in 1961 a three-dimensional equation to describe the temporal evolution of a neuron subjected to an external current $X\colon [0,T] \to \mathbb{R}$.
This model generalizes well to the case of a *network* of interacting neurons (e.g. a small area of the brain), in which case the evolution of the $i$-th neuron $Y^i_t = (v^i_t, w^i_t, c^i_t)$, $i = 1,\dots,N$
is governed by

$$
\begin{cases}
dv^i_t = \Big(v^i_t - \dfrac{(v^i_t)^3}{3} - w_t^i - \dfrac{1}{N}\sum_{j=1}^N (v^i_t - 1)c^j_t\Big) dt + dX^i_t - \dfrac{1}{N}\sum_{j=1}^N (v^i_t - 1)c^j_t\, dB_t^i, \\
dw^i_t = (v^i_t + 1 - w^i_t)\, dt, \\
dc^i_t = (S(v_t^i)(1 - c_t^i) - c_t^i)\, dt
\end{cases} \tag{FHN}
$$

where $B$ is Brownian noise coming from the interactions,
$S(v) = \dfrac{1}{1+\exp(-v)}$, while $dX_t = \alpha_t\, dt + d\tilde{B}_t$ is a control for an independent brownian $\tilde{B}$ (external noise).
The mathematical treatment of Eq. (FHN) (and of its mean-field limit Eq. (RSDE)) is still in its infancy because the coefficients are not Lipschitz.
From the point of view of concrete applications, the model Eq. (FHN) is motivated by the treatment of neural diseases (in this model, $X_t$ models an external current whose purpose is to generate a given brain response).
Despite our contribution [hocquet2020optimal] the problem of approximation of an optimal control (for a given cost functional $J(X)$) remains largely open.

A current research topic is the weak error analysis when the Wiener measure is replaced by a simpler probability measure which nevertheless preserves some quantities of interest. An example is the *cubature* method introduced by Lyons and Victoir [lyons2004cubature]. An attempt in this direction was made in [hocquet2022weak] (with the approximation of the control problem for Eq. (FHN) as a horizon). We derived weak convergence rates for classical SDEs from a novel argument, based on the multiplicative sewing lemma of [gerasimovics2021non]. It seems to be flexible enough to include the full ansatz Eq. (RSDE), which I want to address in the future.

### Hybrid rough and stochastic differential equations (2022–2024)

When $N \gg 1$, the chaos propagation result of [baladron2012mean]
implies that the dynamics of a single neuron $Y_t$ can be approximated by a
McKean-Vlasov equation of the form

$$
\begin{cases}
dY_t = b(Y_t,\mu_t)\, dt + \sigma(Y_t,\mu_t)\, dB_t + f(Y_t,\mu_t)\, d\mathbf{X}_t, \quad \text{on } (s,T], \\
\mu_t = \mathcal{L}(Y_t), \\
Y_s = \xi.
\end{cases} \tag{RSDE}
$$

where for fixed $t$ the term $\mu_t$ denotes the law of the random variable $Y_t$,
$b$ is a non-linearity, $\sigma$ a diffusion matrix and $B$ a standard multidimensional
Brownian motion, while $\mathbf{X}$ is a given control.
The ansatz Eq. (RSDE) actually covers a wide variety of applications which go much
beyond control theory. For instance, in the theory of filtering, the input $\mathbf{X}$
can be thought as a frozen realization of an additional, observed source of noise.
In recent works with Peter Friz and Khoa Lê [friz2021rough; friz2022mckean],
we have developed a notion of stochastic rough differential equation which reduces
exactly to an Itô equation (resp. to a rough differential equation) when
$f$ (resp. $\sigma$) is taken equal to zero. In doing so, we have been
forced to revise the main concepts of classical stochastic and rough analysis
and to introduce the corresponding mixed objects.

## Events

### Randomness, PDEs and Nonlinear Fluctuations – Fall 2019
**Type:** Scholarship
**Location:** Bonn University

Scholarship award as participant and group leader, from the University of Bonn, to participate in the Junior Trimester Program *Randomness, PDEs and Nonlinear Fluctuations* (Coordinator: Prof. Massimiliano Gubinelli).
Organization of 2 workshops.

**Link:** https://him-application.uni-bonn.de/uploads/media/report_HOCQUET-group4.pdf

### Harmonic analysis and rough paths – Nov. 18–19, 2019
**Type:** Workshop
**Location:** Bonn University

(With Peter Friz and Pavel Zorin-Kranich).
The goal of this conference was to further explore the connections between stochastic/rough analysis
on the one hand and harmonic analysis on the other.

**Link:** https://www.him.uni-bonn.de/de/programs/past-programs/past-junior-trimester-programs/randomness-pdes-fluctuations-2019/workshop-harmonic-analysis-and-rough-paths-november-18-19-2019/

### Problems of roughness, geometry and random fluctuations – Dec. 9–12, 2019
**Type:** Workshop
**Location:** Bonn University

(With Khoa Lê).
This conference aimed to bring together different communities in the field of stochastic differential equations in finite or infinite dimension.
Various experts such as A. Thalmaier, M. Röckner, X-M. Li, H. Oberhauser, C. Litterer, G. Iyer, K-T. Sturm, P. Mörters, L. Coutin and A. Deya (among others) were invited,
which made it possible to bring together independently developing theories. Many discussions took place during the coffee breaks.

**Link:** https://www.him.uni-bonn.de/de/programs/past-programs/past-junior-trimester-programs/randomness-pdes-fluctuations-2019/problems-of-roughness-geometry-and-random-fluctuations/

### Stochastic optimal control of interacting particle systems – 10 Jan., 2020
**Type:** Workshop
**Location:** Technische Universität Berlin

Mini-symposium organized with Wilhelm Stannat and Alexander Vogler.

**Link:** https://www.itp.tu-berlin.de/collaborative_research_center_910/sonderforschungsbereich_910/events/symposia/stochastic_optimal_control_of_interacting_particle_systems_100120/

### New directions in rough paths theory – Dec. 7–12, 2020
**Type:** Workshop reporter
**Location:** Oberwolfach, Germany

Organization and report of the Oberwolfach meeting 2050a.
The goal of this meeting was to bring together the main experts in rough paths theory, to discuss recent developments and future directions.

**Link:** https://www.mfo.de/occasion/2050a/www_view

## Talks

Presentations given at conferences and other events (excluding seminars):

- 06.06.2013, Grenoble. *A semi-discrete scheme for the stochastic Landau-Lifshitz-Gilbert equation.* Mini-conférence ANR-micromanip.
- 11.07.2015, Saint-Flour. *Finite-time blow-up for the stochastic LLG on the unit disk.* 45th Probability Summer School (6–17 Jul. 2015), 7 rue des Planchettes, Saint-Flour, France.
- 12.08.2016, Weierstrass Insitute, Berlin. *Large time behaviour of the stochastic harmonic map flow.* 5th Berlin-Oxford meeting.
- 10.10.2016, Bielefeld. *Large time behaviour of the stochastic harmonic map flow.* Stochastic Partial Differential equations (Oct. 10–14, 2016). Conference in honor of Michael Röckner's 60th birthday, Bielefeld, Germany.
- 28.09.2017, Bielefeld. *Recent results on the stochastic LLG in 2 or 3 dimensions.* Stochastic spin systems: models, theory, simulation and real world applications (Sep. 28–30, 2017). University of Bielefeld, Germany.
- 18.05.2017, Weierstrass Institute, Berlin. *The energy method for rough partial differential equations.* 7th Annual ERC Berlin-Oxford Young Researchers Meeting on Applied Stochastic Analysis (May 18–20, 2017). Weierstrass Institute, Berlin.
- 16.12.2017. *Itô formula for RPDEs and boundedness of solutions.* 8th Oxford-Berlin Young Researchers Meeting on Applied Stochastic Analysis (Dec. 14–16, 2017). University of Oxford.
- 9th Annual ERC Berlin-Oxford Young Researchers Meeting on Applied Stochastic Analysis (Jun. 14–16, 2018). Weierstrass Institute, Berlin.
- 29.11.2018. *A multiplicative sewing Lemma and some by-products.* 10th Oxford-Berlin Young Researchers Meeting on Applied Stochastic Analysis (Nov. 29 – Dec. 1st 2018). University of Oxford.
- 16.01.2019. *A multiplicative sewing Lemma and applications.* Berlin-Leipzig workshop in analysis and stochastics (Jan. 15–18, 2019). Max-Planck-Institut für Mathematik, Leipzig, Germany.
- 24.05.2019. *Hybrid rough and stochastic differential equations.* 11th Oxford-Berlin Young Researchers Meeting on Applied Stochastic Analysis (May 23–25, 2019). Weistrass Institute, Berlin.
- 18.11.2019. *Quasilinear rough partial differential equations with transport noise.* Harmonic Analysis and rough paths (Oct. -18, 2019), HIM, Bonn (speaker and organisor).
- 10.01.2020, Technische Universität Berlin. *Optimal control of mean-field equations with monotone coefficients and applications in neurosciences.* Mini-symposium Interacting particle systems.
- 15.10.2020. *Monoid-valued sewing lemmata and applications.* Higher structures emerging from renormalisation, ESI Vienna (online meeting, Oct. 12–16, 2020).
- 09.03.2021. *Monoid-valued sewing lemmata and applications.* Pathwise Stochastic Analysis and Applications, CIRM (virtual conference, March 8–12, 2021).

## Seminars

Invited seminar talks at laboratories:

- 11.02.2016, Amiens. *Singularités du flot stochastique des applications harmoniques.* Séminaire de probabilités. Invitation: Olivier Goubet.
- 05.07.2016, Pisa. *Finite-time singularities of the stochastic harmonic map flow on surfaces.* Probability seminar. Invitation: Marco Romito.
- 16.05.2017, Aachen. *Finite-time singularities of the stochastic harmonic map flow on surfaces.* Probability seminar.
- 30.05.2017, Nice. *Finite-time singularities of the stochastic harmonic map flow on surfaces.* Séminaire de probabilités. Invitation: Roland Diel.
- 13.11.2017, York. *A variational approach to partial differential equations driven by a rough path.* Probability seminar. Invitation: Zdzislaw Brzezniak.
- 22.11.2017, Bielefeld. *Itô formula for RPDEs and boundedness of solutions.* Probability seminar. Invitation: Martina Hofmanová.
- 29.11.2017, Tübingen. *Rough paths and Stochastic Calculus (a digest).* Probability seminar. Invitation: Andreas Prohl.
- 14.05.2018, Oxford. *Unbounded rough drivers, Sobolev spaces and Moser iteration.* Probability Seminar.
- 10.01.2019, Berlin. *Rough stochastic analysis.* Probability Seminar.
- 23.02.2020, Université Paul Sabatier, Toulouse. *Hybrid differential equations and applications.* Séminaire d'Analyse. Invitation: Vincent Feuvrier.

## Posters

Poster contributions on Mathematical Physics (Landau–Lifshitz) presented at international workshops; details available on request.

## Skills – Programming

Proficiency on a 0–5 scale.

| Language | Proficiency |
|---|---|
| Python | 4.7 |
| SQL | 4.0 |
| C++ | 3.5 |
| Rust | 3.0 |
| R | 2.5 |

## Skills – Scientific Software

Proficiency on a 0–5 scale.

| Software | Proficiency |
|---|---|
| MATLAB | 5.0 |
| FreeFem++ | 5.0 |
| SciPy | 4.0 |

## MLOps

Proficiency on a 0–5 scale.

| Function | Tool(s) | Proficiency |
|---|---|---|
| Development and debugging | VS Code | 4.5 |
| Containerization | Docker | 3.5 |
| Version control & CI/CD | Git, GitHub Actions, Pytest | 4.5 |
| OS & Scripting | Linux, Bash | 4.5 |
| AI tools | Copilot, Windsurf, Google Colab | 3.5 |
| Cloud-based ML workflows | GCP, AWS, Azure | 2.5 |

## Math Keywords

Proficiency on a 0–5 scale.

| Keyword | Proficiency |
|---|---|
| Probability Theory | 5.0 |
| Stochastic Analysis | 5.0 |
| Statistics | 4.0 |
| Partial differential equations | 3.5 |
| Rough Paths | 4.5 |
| Control | 4.0 |
| Numerical Analysis | 3.5 |

## Keywords

- Stochastic Analysis
- Itô calculus
- Diffusions
- Partial Differential Equations
- Rough Partial Differential Equations
- Stochastic Partial Differential Equations
- Stochastic Control
- Rough Stochastic Equations
- Rough Paths
- Numerical analysis
- Interacting Particle Systems
- Mean-Field Stochastic Differential Equations
- Mathematical physics
- Micromagnetism
- Liquid crystals
- Neuroscience

## Teaching Skills

### Bilingual & intercultural teaching
Mathematics instruction in French (native) and English (fluent); German (B2, certificate July 2025). Experience teaching foreign newcomers in the **EV2** mathematics course at École Polytechnique.

### Teaching & assessment
Lecturing and tutorials at university level; design, correction, and grading of exams and assignments; detailed feedback; supervision of Master's theses and projects.

### Digital tools for teaching
Python (NumPy, pandas, Matplotlib), Jupyter, MATLAB, FreeFem++, Scilab; creation of simulations/visualisations to support learning.

### Online teaching
Experience with online teaching platforms (Zoom) and tools (Google Classroom) for remote learning.

### AI in education
Integration of AI tools (e.g., ChatGPT) to enhance learning experiences and provide personalized support.

### Collaboration
Course co-design, seminar organisation, and teamwork within international academic environments.

## Soft Skills

- Analytical thinking
- Problem-solving
- Perseverance
- Rigor
- Adaptability
- Clear Communication
- Teamwork
- Time Management
- Creativity
- Attention to Detail
- Critical Thinking
- Scientific Writing
- Interdisciplinary Collaboration
- Mentoring and Coaching
- Lecture Preparation
- Exam Preparation
- Enthusiasm for Teaching
- Conveying Complex Ideas with Simple Words
- Science Communication
- Public Speaking

## Graphs

Visual assets illustrating the work above (referenced here by title; image files are not part of this text corpus).

### eee
Simulation example: Spontaneous reversal of magnetization (Blow-up). From left ($t=0$) to right ($t=1$s):
the energy of the system concentrates at the disk's center as time passes.

### fhn
Neural control example: FitzHugh-Nagumo neuron model with optimal control. From left to right:
Membrane potential, adjoint state and optimal control for a population of neurons.

## Key Points

- **[Graduation Cap]** Mathematician with strong academic background; Strong publication record in stochastic analysis, PDEs, and control theory.
- **[User Graduate]** Capacity to address complex problems with a rigorous mathematical approach.
- **[Hands]** Research rooted in applications (e.g. micromagnetism, fluid mechanics).
- **[Handshake]** Collaborative mindset; Proven experience working in international research teams with multicultural backgrounds.
- **[Laptop Code]** Frequent numerical experiments; strong programming skills in Python.
- **[Certificate]** Certification at MIT Professional Education (Applied Data Science Program); capstone project on recommender systems.
- **[User Tie]** Hands-on experience in data science pipelines.
- **[Brain]** Deep knowledge of the mathematics behind machine learning (ML, DL and GenAI).
- **[Cogs]** MLOps best practices.
- **[Code]** Strong sense of what *good code* looks like and how to structure it; portfolio mindset.
- **[Comments]** Ability to communicate complex ideas clearly through teaching and public speaking.
- **[Cloud]** Growing knowledge of cloud-based ML workflows (GCP, Azure).
- **[Language]** Native language **French**, fluent in **English**, and conversational **German** (B2-C1, with B2 diploma).
- **[Chalkboard Teacher]** Qualified secondary school mathematics teacher with a Master degree in Mathematics and the French *Agrégation* (national teaching qualification).
- **[University]** Experienced across various university levels, including undergraduate and graduate courses.
- **[Language]** Multilingual instruction in English and French; Keen to teach in German and actively progressing (**B2** certificate obtained in July).
- **[Users]** Passionate about making mathematics concrete and motivating through hands-on activities, small-group work, and modern pedagogy.

## Miscellaneous

**Nationality:** French

**Spoken languages:** French (native), English (fluent), German (B2 Diploma)

**Personal status:** Married, 2 children.

**Titles/Affiliation:** Researcher | Postdoctoral fellow | Technische Universität

**Further training (Coursera):** Web scraping, interactive dashboards, Basics of RAG and LangChain, Git/GitHub workflows, prompting techniques for GenAI, MLOps tools, basic Rust for ML.

**References:** Available upon request; (former supervisors: Friz: `friz@math.tu-berlin.de`, De Bouard: `anne.debouard@polytechnique.edu`, Hofmanová: `hofmanova@math.uni-bielefeld.de`, Stannat: `stannat@math.tu-berlin.de`)

**Google Scholar:** https://scholar.google.com/citations?user=Z4gS7yEAAAAJ&hl=en

**Geographical availability:** Willing to relocate if necessary (e.g., Munich, Frankfurt, Leipzig etc; Anywhere in Europe or in UK); open to remote work.

**Interests:** Astrophysics, theoretical physics, piano/guitar, telescope sky-watching, football, running, cooking, reading, history, traveling, spending time with family.

**References:** Available upon request; Or ask directly to my former project supervisors:
- Peter Friz: `friz@math.tu-berlin.de`
- Anne De Bouard: `anne.debouard@polytechnique.edu`
- Martina Hofmanová: `hofmanova@math.uni-bielefeld.de`
- Wilhelm Stannat: `stannat@math.tu-berlin.de`

**Further training (Coursera):** Web scraping, interactive dashboards, Basics of RAG and LangChain, Git/GitHub workflows, prompting techniques for GenAI, MLOps tools, basic Rust for ML.

**IBM Data Science Professional Certificate:** Additional certification completed in Nov. 2024 (IBM Skills Network / Coursera).
Comprehensive 10-course track that emphasized relational databases
(SQL), CRISP-DM methodology, and creating interactive dashboards
using Dash. Gained hands-on experience with web scraping
(Beautiful Soup), geographic visualizations (Folium), and version control
via Git/GitHub. Also explored R and RStudio to broaden
data analysis capabilities beyond Python.

## CV Sections

Top-level sections of the original CV template:

- Personal Information
- Key points about me
- Education and Training
- Skills
- Project description
- Publication list
- Oral Communications
- Teaching portfolio
- Teaching statement
- Numerical portfolio

## CV Subsections

Subsections used within the sections above:

- Professional Experience
- Mathematical expertise
- Programming expertise
- Scientific Softwares
- Softskills
- MLOps and DevOps tools
- Keywords
- Major events in scientific career
- Conferences
- Invited seminars
- A personal reflection note on the practice of teaching
