#!/usr/bin/env swipl
% check-journal.pl -- strict clause-floor gate for append-only Prolog journals.
%
% WHY CLAUSE-COUNT FLOORS: SWI-Prolog recovers past syntax-corrupted terms and
% keeps loading, so a consulted journal whose predicates merely exist proves
% nothing about completeness -- a truncated or corrupted region simply
% vanishes while earlier clauses stay asserted. This exact failure hid 11
% corrupt entries in a production journal for weeks while existence-only
% checks kept passing. Minimum clause counts per predicate turn "it loaded"
% into "every expected region of the journal is present".
%
% Usage (cwd-independent; pass an absolute journal path):
%   swipl check-journal.pl -- <journal.pl> [floors.pl]
%   CHECK_JOURNAL_FLOORS=<floors.pl> swipl check-journal.pl -- <journal.pl>
%
% Floors file resolution, first match wins:
%   1. optional second argv path (explicit)
%   2. $CHECK_JOURNAL_FLOORS (explicit)
%   3. <owner>/checks/floors.pl when the journal lives under <owner>/runs/<Run>/
%   4. <journal-dir>/floors.pl
% An explicit floors file that is missing or unreadable is a usage error
% (exit 2). Conventional candidates that do not exist mean "no floors
% declared": only journal load integrity is checked then.
%
% Floors file contents (facts):
%   min_clauses(<name>/<arity>, <minimum>).  % >= minimum clauses after loading
%   required_entry(<term-template>).         % >= one loaded clause unifies
%
% Example floors for a prolog-verify run journal kept at
% <root>/.prolog/runs/<Run>/evidence.pl (so candidate 3 finds it):
%   min_clauses(machine_observation/8, 11).
%   required_entry(machine_observation(_, _, _, _, exit(0), _, _, _)).
%
% Exit codes: 0 = pass; 1 = floor or required-entry failure (including corrupt
% journals whose loaded counts fall below their floors); 2 = usage error,
% unreadable journal, or a journal that failed to load cleanly without any
% floor catching it.
%
% KNOWN SWI PITFALL (hit live 2026-11-12): halt/1 inside catch/3 throws
% unwind(halt(N)) and the catch swallows it. halt/1 is only called from main/0
% outside every catch/3; load errors are reported and fail instead.

:- initialization(main, main).

main :-
    (   gate(Exit) -> true
    ;   Exit = 2
    ),
    halt(Exit).

gate(Exit) :-
    parse_args(Journal, FloorsArgv),
    resolve_floors(Journal, FloorsArgv, Floors),
    prepare_floors(Floors),
    (   load_journal(Journal) -> LoadFailed = false
    ;   LoadFailed = true
    ),
    floor_failures(Low, Missing),
    report(Low, Missing),
    verdict(LoadFailed, Low, Missing, Exit).

parse_args(Journal, FloorsArgv) :-
    current_prolog_flag(argv, Argv),
    (   Argv = [--|Rest] -> true
    ;   Rest = Argv
    ),
    (   Rest = [Journal|FloorsArgv] ->
        atom(Journal)
    ;   format(user_error, "usage: swipl check-journal.pl -- <journal.pl> [floors.pl]~n", []),
        fail
    ).

resolve_floors(Journal, FloorsArgv, Floors) :-
    (   FloorsArgv = [First|_]
    ->  Floors = explicit(First)
    ;   getenv('CHECK_JOURNAL_FLOORS', Env), Env \== ''
    ->  Floors = explicit(Env)
    ;   conventional_floors(Journal, Floors)
    ).

conventional_floors(Journal, Floors) :-
    file_directory_name(Journal, JournalDir),
    file_directory_name(JournalDir, Parent),
    (   file_base_name(Parent, runs)
    ->  file_directory_name(Parent, Owner),
        directory_file_path(Owner, 'checks/floors.pl', OwnerFloors),
        Candidates = [OwnerFloors, JournalDir/'floors.pl']
    ;   Candidates = [JournalDir/'floors.pl']
    ),
    first_existing(Candidates, Floors).

first_existing([], none) :-
    !,
    format(user_output, "check-journal: no floors file; checking load integrity only~n", []).
first_existing([Candidate|Rest], Floors) :-
    (   exists_file(Candidate)
    ->  Floors = conventional(Candidate)
    ;   first_existing(Rest, Floors)
    ).

prepare_floors(explicit(Floors)) :-
    !,
    (   exists_file(Floors)
    ->  consult_quietly(Floors, floors)
    ;   format(user_error, "check-journal: floors file not found: ~w~n", [Floors]),
        fail
    ).
prepare_floors(conventional(Floors)) :-
    !,
    consult_quietly(Floors, floors).
prepare_floors(none).

consult_quietly(Path, What) :-
    catch(consult(Path),
          Error,
          (   format(user_error, "check-journal: ~w failed to load: ", [What]),
              print_message(error, Error),
              fail
          )).

load_journal(Journal) :-
    (   exists_file(Journal)
    ->  true
    ;   format(user_error, "check-journal: journal not found: ~w~n", [Journal]),
        fail
    ),
    consult_quietly(Journal, journal).

floor_failures(Low, Missing) :-
    (   predicate_property(min_clauses(_, _), defined)
    ->  findall(min_clauses(Pred, Floor, Have),
                (   min_clauses(Pred, Floor),
                    clause_count(Pred, Have),
                    Have < Floor
                ),
                Low)
    ;   Low = []
    ),
    (   predicate_property(required_entry(_), defined)
    ->  findall(required_entry(Template),
                (   required_entry(Template),
                    \+ entry_present(Template)
                ),
                Missing)
    ;   Missing = []
    ).

clause_count(Name/Arity, Have) :-
    (   functor(Head, Name, Arity),
        predicate_property(Head, number_of_clauses(Have))
    ->  true
    ;   Have = 0
    ).

entry_present(Template) :-
    catch(clause(Template, _), error(existence_error(_, _), _), fail).

report(Low, Missing) :-
    forall(member(min_clauses(Pred, Floor, Have), Low),
           format(user_error, "check-journal: FAIL ~w has ~w clauses, floor is ~w~n",
                  [Pred, Have, Floor])),
    forall(member(required_entry(Template), Missing),
           format(user_error, "check-journal: FAIL no journal entry matches ~q~n", [Template])),
    length(Low, LowCount),
    length(Missing, MissingCount),
    (   LowCount + MissingCount =:= 0
    ->  format(user_output, "check-journal: journal floors satisfied~n", [])
    ;   format(user_error, "check-journal: ~w floor failures, ~w missing entries~n",
               [LowCount, MissingCount])
    ).

verdict(false, [], [], 0) :-
    !.
verdict(true, [], [], 2) :-
    !,
    format(user_error, "check-journal: journal failed to load and no floor caught it~n", []).
verdict(_, _, _, 1).
